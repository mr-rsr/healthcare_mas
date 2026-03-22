from langchain_aws import ChatBedrockConverse, BedrockEmbeddings

embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0")
llm = ChatBedrockConverse(model="us.anthropic.claude-3-5-sonnet-20241022-v2:0")