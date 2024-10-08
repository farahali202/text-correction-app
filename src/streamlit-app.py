import streamlit as st
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch
import os
from nltk.translate.bleu_score import sentence_bleu
from rouge import Rouge

# Set up the path to the model directory
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','Model'))

# Check if the model directory exists
if not os.path.exists(model_path):
    st.error(f"Model directory not found at {model_path}. Please ensure the 'Model' directory is present.")
    st.stop()

# Check for required model files
required_files = ['model.pth', 'spiece.model', 'tokenizer_config.json', 'config.json']
missing_files = [file for file in required_files if file not in os.listdir(model_path)]

# Debugging: Print the missing files, if any
if missing_files:
    st.error(f"The following required files are missing from the model directory: {', '.join(missing_files)}")
    st.stop()

# Load the model and tokenizer
@st.cache_resource
def load_model_and_tokenizer():
    try:
        # Load the T5 model and tokenizer from the directory
        model = T5ForConditionalGeneration.from_pretrained(model_path)  # Load model configuration
        model.load_state_dict(torch.load(os.path.join(model_path, 'model.pth'), map_location=torch.device('cpu')))
        tokenizer = T5Tokenizer.from_pretrained(model_path)  # Load tokenizer files (including spiece.model)
        return model, tokenizer
    except Exception as e:
        st.error(f"Error loading model or tokenizer: {str(e)}")
        st.stop()

# Load the model and tokenizer
model, tokenizer = load_model_and_tokenizer()

# Define the text correction function
def correct_text(input_text):
    input_ids = tokenizer("correct: " + input_text, return_tensors="pt", padding=True, truncation=True).input_ids
    outputs = model.generate(input_ids, max_length=128)
    corrected_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return corrected_text

# Function to calculate BLEU and ROUGE scores
def calculate_performance_scores(original, corrected):
    # Calculate BLEU score
    bleu_score = sentence_bleu([original.split()], corrected.split())
    
    # Calculate ROUGE scores
    rouge = Rouge()
    scores = rouge.get_scores(corrected, original)
    rouge_1 = scores[0]['rouge-1']['f']
    rouge_2 = scores[0]['rouge-2']['f']
    rouge_l = scores[0]['rouge-l']['f']
    
    return bleu_score, rouge_1, rouge_2, rouge_l

# Streamlit app interface
st.title("📝 Text Correction App")
st.write("### Improve your writing by correcting grammatical errors!")
st.write("Enter the text with grammatical errors below and click 'Get Correction'.")

# User input
user_input = st.text_area("Input Text", placeholder="Type or paste your text here...")

# Initialize performance scores
bleu_score = 0.0
rouge_1 = 0.0
rouge_2 = 0.0
rouge_l = 0.0

# Button to trigger the correction
if st.button("Get Correction"):
    if user_input:
        with st.spinner("Correcting text..."):
            corrected_output = correct_text(user_input)
            # Calculate performance scores
            bleu_score, rouge_1, rouge_2, rouge_l = calculate_performance_scores(user_input, corrected_output)
        
        st.subheader("Corrected Text:")
        st.write(corrected_output)
    else:
        st.warning("Please enter some text.")

# Sidebar for performance scores
st.sidebar.header("Performance Scores")
st.sidebar.write(f"**BLEU Score:** {bleu_score:.4f}")
st.sidebar.write(f"**ROUGE-1 Score:** {rouge_1:.4f}")
st.sidebar.write(f"**ROUGE-2 Score:** {rouge_2:.4f}")
st.sidebar.write(f"**ROUGE-L Score:** {rouge_l:.4f}")

# Footer for additional information
st.markdown("---")
st.write("This app uses a fine-tuned T5 model for text correction.")
