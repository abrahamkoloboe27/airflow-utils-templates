from setuptools import setup, find_packages

setup(
    name="airflow-alerts",
    version="1.0.0",
    description="Modular Airflow alert templates for email and Google Chat notifications",
    author="Abraham Koloboe",
    packages=find_packages(exclude=["tests*", "dags*"]),
    include_package_data=True,
    package_data={
        "": ["templates/**/*.html", "templates/**/*.j2"],
    },
    install_requires=[
        "apache-airflow>=2.0.0",
        "jinja2>=3.0.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
        ],
    },
    python_requires=">=3.7",
)
