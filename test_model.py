import openai

# Insira sua chave de API da OpenAI aqui
OPENAI_API_KEY = "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"

# Configuração do modelo a ser testado
MODELOS = ["gpt-3.5-turbo", "gpt-4"]

def testar_modelos():
    openai.api_key = OPENAI_API_KEY
    
    for modelo in MODELOS:
        print(f"\nTestando o modelo: {modelo}")
        try:
            # Solicitação para o modelo especificado
            response = openai.ChatCompletion.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": "Você é um assistente virtual."},
                    {"role": "user", "content": "Qual modelo você está utilizando? Responda de forma clara."}
                ]
            )
            
            # Processar e exibir a resposta
            resposta = response["choices"][0]["message"]["content"]
            modelo_retornado = response["model"]
            print(f"Modelo retornado pela API: {modelo_retornado}")
            print(f"Resposta do modelo: {resposta}")
        
        except openai.InvalidRequestError as e:
            print(f"Erro ao testar o modelo {modelo}: {e}")
        
        except openai.AuthenticationError as e:
            print(f"Erro de autenticação: {e}")
        
        except openai.OpenAIError as e:
            print(f"Erro geral da OpenAI: {e}")
        
        except Exception as e:
            print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    testar_modelos()
