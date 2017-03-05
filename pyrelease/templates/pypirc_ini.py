TEMPLATE = """[distutils]
index-servers=
    pypi
    testpypi

[testpypi]
repository = https://testpypi.python.org/pypi
username = {pypi_username}

[pypi]
repository = https://pypi.python.org/pypi
username = {pypi_username}\n
"""
