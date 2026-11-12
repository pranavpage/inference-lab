# just a set of commands to run on a GPU instance to get started with vllm
export HF_HOME=/workspace/hf
export HF_TOKEN=hf_Your
echo "Please set HF_TOKEN"
git clone https://github.com/pranavpage/inference-lab.git && cd inference-lab

pip install uv
uv venv ~/vllm-env && source ~/vllm-env/bin/activate
uv pip install vllm openai
vllm --version
