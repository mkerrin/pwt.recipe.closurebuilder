import sys
import os.path
import hashlib

# Import the depswrite and source from closure-library checkout
old_path = sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "build"))
import depswriter
import depstree
import source
import treescan
import closurebuilder
import jscompiler
# reset the path
sys.path = sys.path[:-1]

class Source(source.Source):

    def __init__(self, path):
        super(Source, self).__init__(source.GetFileContents(path))

        self._path = path

    def GetPath(self):
        return self._path

    def GetSourcePath(self):
        return self._source, self._path


class Deps(object):
    """
    depswriter abstraction
    """

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options

        self.output = options["output"]

    def _getRelativePathToSourceDict(self, root, prefix = ""):
        start_wd = os.getcwd()
        os.chdir(root)

        path_to_source = {}
        for path in treescan.ScanTreeForJsFiles("."):
            prefixed_path = depswriter._NormalizePathSeparators(
                os.path.join(prefix, path)
                )
            path_to_source[prefixed_path] = Source(
                os.path.join(start_wd, root, path)
                )

        os.chdir(start_wd)

        return path_to_source

    def find_path_to_source(self):
        path_to_source = {}

        # Roots without prefixes
        for root in self.options.get("roots", "").split("\n"):
            if not root:
                continue

            path_to_source.update(
                self._getRelativePathToSourceDict(root)
                )

        # Roots with prefixes
        for root_with_prefix in \
                self.options.get("root_with_prefix", "").split("\n"):
            if not root_with_prefix:
                continue

            root, prefix = depswriter._GetPair(root_with_prefix)
            path_to_source.update(
                self._getRelativePathToSourceDict(root, prefix = prefix)
                )

        # Source paths with alternate deps paths
        for path_with_depspath in \
                self.options.get("paths_with_depspath", "").split("\n"):
            if not path_with_depspath:
                continue

            srcpath, depspath = depswriter._GetPair(path_with_depspath)
            path_to_source[depspath] = source.Source(
                source.GetFileContents(srcpath)
                )

        return path_to_source

    def install(self):
        self.path_to_source = self.find_path_to_source()

        out = open(self.output, "w")
        out.write(
            "// This file was autogenerated by buildout[%s].\n" % self.name)
        out.write("// Please do not edit.\n")

        out.write(depswriter.MakeDepsFile(self.path_to_source))

        return (self.output,)


class Compile(object):

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options

        self.dependency = options["dependency"]
        self.compiler_jar = options.get(
            "jar", os.path.join(os.path.dirname(__file__), "compiler-801.jar"))
        self.compiler_flags = [
            flag for flag in options.get("flags", "").split() if flag
            ]
        self.outputdir = self.options["output"]

    def get_base(self, sources):
        base = self.options.get("base.js", "/closure/closure/goog/base.js")
        return self.buildout[self.dependency].recipe.path_to_source[base]

    def install(self):
        self.path_to_source = self.buildout[self.dependency].recipe.path_to_source
        sources = self.path_to_source.values()
        tree = depstree.DepsTree(sources)

        base = closurebuilder._GetClosureBaseFile(sources)

        start_wd = os.getcwd()

        input_namespaces = set()
        for input_path in self.options.get("inputs", "").split():
            if not input_path:
                continue

            js_input = [
                source
                for source in sources
                if source.GetPath() == os.path.join(start_wd, input_path)
                ]
            if len(js_input) != 1:
                # logging.error('No source matched input %s', input_path)
                raise Exception("No source matched input %s" % input_path)

            input_namespaces.update(js_input[0].provides)

        input_namespaces.update(
            [namespace
             for namespace in self.options.get("namespaces", "").split()
             if namespace]
            )

        if not input_namespaces:
            raise Exception(
                "No namespaces found. At least one namespace must be "
                "specified with the --namespace or --input flags.")

        deps = [base] + tree.GetDependencies(input_namespaces)

        compiled_code = jscompiler.Compile(
            self.compiler_jar,
            [js_source.GetSourcePath()[1] for js_source in deps],
            self.compiler_flags)

        md5name = hashlib.md5()
        md5name.update(compiled_code)
        filename = md5name.hexdigest()

        open(
            os.path.join(self.outputdir, filename + ".js"), "w") \
            .write(compiled_code)

        return (filename,)
