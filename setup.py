from setuptools import find_packages, setup

setup(
    name = "pwt.recipe.closurebuilder",
    version = "0.9",
    author = "Michael Kerrin",
    author_email = "michael.kerrin@gmail.com",

    description = "zc.buildout recipe for closurebuilder",
    long_description = open("src/pwt/recipe/closurebuilder/README.txt").read(),
    url = "https://github.com/mkerrin/pwt.recipe.closurebuilder",

    packages = find_packages("src"),
    package_dir = {"": "src"},

    install_requires = ["setuptools",
                        "zc.buildout",
                        ],
    extras_require = {
        "test": ["zope.testing"],
        },

    entry_points = """
[zc.buildout]
dependency = pwt.recipe.closurebuilder:Deps
compile = pwt.recipe.closurebuilder:Compile
""",

    include_package_data = True,
    zip_safe = False,

    test_suite = "pwt.recipe.closurebuilder.tests.test_suite",
    )
