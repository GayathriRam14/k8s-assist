# python_ollama_server.py - Ollama-compatible server using Python Llama3
from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import threading
import time

app = Flask(__name__)

class PythonOllamaServer:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_name = "llama3"
        self.loading = False
        self.load_model()
    
    def load_model(self):
        """Load Llama3 model in background"""
        if self.loading:
            return
        
        self.loading = True
        
        def _load():
            try:
                print("🔄 Loading Llama3 model... (this may take a few minutes)")
                
                # Try different model options in order of preference
                model_options = [
                    "unsloth/llama-3-8b-bnb-4bit",      # Pre-quantized, smaller
                    "microsoft/DialoGPT-medium",         # Smaller fallback
                    "distilgpt2"                         # Tiny fallback
                ]
                
                for model_name in model_options:
                    try:
                        print(f"  Trying {model_name}...")
                        
                        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                        
                        if "llama" in model_name.lower():
                            self.model = AutoModelForCausalLM.from_pretrained(
                                model_name,
                                torch_dtype=torch.float16,
                                device_map="auto",
                                load_in_4bit=True
                            )
                        else:
                            self.model = AutoModelForCausalLM.from_pretrained(
                                model_name,
                                torch_dtype=torch.float16
                            )
                        
                        if self.tokenizer.pad_token is None:
                            self.tokenizer.pad_token = self.tokenizer.eos_token
                        
                        print(f"✅ Successfully loaded {model_name}")
                        break
                        
                    except Exception as e:
                        print(f"  ❌ Failed to load {model_name}: {e}")
                        continue
                
                if not self.model:
                    print("❌ Failed to load any model")
                
            except Exception as e:
                print(f"❌ Model loading error: {e}")
            finally:
                self.loading = False
        
        # Load model in background thread
        threading.Thread(target=_load, daemon=True).start()
    
    def generate_response(self, messages, model="llama3"):
        """Generate response compatible with Ollama chat API"""
        
        if not self.model or not self.tokenizer:
            return {
                "error": "Model not loaded yet, please wait..."
            }
        
        try:
            # Extract user message (Ollama format)
            user_message = ""
            for msg in messages:
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            if not user_message:
                return {"error": "No user message found"}
            
            # Generate response
            inputs = self.tokenizer.encode(user_message, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 200,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    no_repeat_ngram_size=2
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response_text = generated_text[len(user_message):].strip()
            
            # Return in Ollama format
            return {
                "model": model,
                "created_at": "2024-01-01T00:00:00Z",
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "done": True
            }
            
        except Exception as e:
            return {
                "error": f"Generation failed: {str(e)}"
            }

# Global server instance
server = PythonOllamaServer()

@app.route('/api/chat', methods=['POST'])
def chat():
    """Ollama-compatible chat endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        model = data.get('model', 'llama3')
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({"error": "No messages provided"}), 400
        
        # Generate response
        response = server.generate_response(messages, model)
        
        if "error" in response:
            return jsonify(response), 500
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tags', methods=['GET'])
def list_models():
    """Ollama-compatible model list endpoint"""
    models = [
        {
            "name": "llama3",
            "modified_at": "2024-01-01T00:00:00Z",
            "size": 4661224676,
            "digest": "python-implementation"
        }
    ]
    
    return jsonify({"models": models})

@app.route('/api/version', methods=['GET'])
def version():
    """Ollama-compatible version endpoint"""
    return jsonify({"version": "python-ollama-1.0.0"})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    status = "ready" if (server.model and not server.loading) else "loading"
    return jsonify({
        "status": status,
        "model_loaded": server.model is not None,
        "loading": server.loading
    })

if __name__ == '__main__':
    print("🚀 Starting Python Ollama-compatible server...")
    print("📡 Server will be available at: http://localhost:11434")
    print("🔄 Model loading in background...")
    print("💡 Check health at: http://localhost:11434/health")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=11434, debug=False, threaded=True)