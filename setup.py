from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="k8s-assist",
    version="2.0.0",
    author="Gayathri Ram",
    description="Intelligent Kubernetes Assistant with LLM-powered troubleshooting using Llama",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GayathriRam14/k8s-assist",  # Replace with your repo
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: >3.8",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich>=12.0.0",
        "ollama>=0.1.0",
    ],
    entry_points={
        "console_scripts": [
            "k8s-assist=kubectl_ai.cli_new:main",
            "k8s-ai=kubectl_ai.cli_new:main",  # Shorter alias
        ],
    },
    keywords="kubernetes kubectl ai assistant troubleshooting devops llama",
    include_package_data=True,
    zip_safe=False,
)