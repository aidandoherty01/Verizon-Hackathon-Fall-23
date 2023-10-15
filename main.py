import os
import sys
import openai
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.llms import OpenAI
from langchain.vectorstores import Chroma

os.environ["OPENAI_API_KEY"] = "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"

# Enable to save to disk & reuse the model (for repeated queries on the same data)
PERSIST = False

query = None
if len(sys.argv) > 1:
  query = sys.argv[1]
#if persist, then recall previous data
if PERSIST and os.path.exists("persist"):
  print("Reusing index...\n")
  vectorstore = Chroma(persist_directory="persist", embedding_function=OpenAIEmbeddings())
  index = VectorStoreIndexWrapper(vectorstore=vectorstore)
else:
  loader = DirectoryLoader("data/", glob='**/*.json', show_progress=True, loader_cls=TextLoader)
  if PERSIST:
    index = VectorstoreIndexCreator(vectorstore_kwargs={"persist_directory":"persist"}).from_loaders([loader])
  else:
    index = VectorstoreIndexCreator().from_loaders([loader])
#creating chain
llm = ChatOpenAI(model="gpt-3.5-turbo")
retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1})
chain = ConversationalRetrievalChain.from_llm(
  llm=llm,
  retriever=retriever,
)

#hack start
from langchain.agents.agent_toolkits import create_retriever_tool
tool = create_retriever_tool(
    retriever, 
    "phone_data_retriever",
    "Searches and returns phone data"
)
tools = [tool]

memory_key = "history"

from langchain.agents.openai_functions_agent.agent_token_buffer_memory import AgentTokenBufferMemory
memory = AgentTokenBufferMemory(memory_key=memory_key, llm=llm)

from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.schema.messages import SystemMessage
from langchain.prompts import MessagesPlaceholder
system_message = SystemMessage(
  content=(
    "You are a Verizon representative who is knowledgeable about your product."
    "Be kind and respectful to customers."
    "Do your best to answer the questions."
    "Feel free to use any tools available to look up"
    "Relevant information, only if necessary."
  )
)
prompt = OpenAIFunctionsAgent.create_prompt(
  system_message=system_message,
  extra_prompt_messages=[MessagesPlaceholder(variable_name=memory_key)]
)

agent = OpenAIFunctionsAgent(llm=llm, tools=tools, prompt=prompt)

from langchain.agents import AgentExecutor
agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True, return_intermediate_steps=True)
#hack end

#ISSUE: Will run locally but not on a server.
#When deploying on cloud, won't upload the file? (0 files uploaded)
#implementing flask
from flask import Flask
from flask import request
app = Flask(__name__)
@app.route("/")
def index():
  while True:
    #Hottest Fix of All Time
    query = None
    if not query:
      query = request.args.get("query", "")
    if query in ['quit', 'q', 'exit']:
      sys.exit()
    result = agent_executor({"input":query})
    return("""
           <form action="" method="get">
           <input type="text" name="query">
           <input type="submit" value="result">
           </form>""" + "Result: " + result["output"])

if __name__=="__main__":
  app.run(host="127.0.0.1", port=8080, debug=True)