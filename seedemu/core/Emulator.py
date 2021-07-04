from __future__ import annotations
from .Merger import Mergeable, Merger
from .Registry import Registry, Registrable, Printable
from seedemu import core
from typing import Dict, Set, Tuple, List
from sys import stderr
import pickle

class BindingDatabase(Registrable, Printable):
    """!
    @brief Registrable wrapper for Bindings.

    classes needs to be Registrable to be saved in the Registry. wrapping
    bindings database with Registrable allows the bindings to be preserved in
    dumps.
    """

    db: List[core.Binding]

    def __init__(self):
        """!
        @brief Create a new binding database.
        """

        ## Binding database
        self.db = []

    def print(self, indentation: int) -> str:
        """!
        @brief get printable string.

        @param indentation indentation.

        @returns printable string.
        """

        return ' ' * indentation + 'BindingDatabase\n'

class LayerDatabase(Registrable, Printable):
    """!
    @brief Registrable wrapper for Layers.

    classes needs to be Registrable to be saved in the Registry. wrapping
    layers database with Registrable allows the layers to be preserved in dumps.
    """

    db: Dict[str, Tuple[core.Layer, bool]]

    def __init__(self):
        """!
        @brief Build a new layers database.
        """

        ## Layers database
        self.db = {}

    def print(self, indentation: int) -> str:
        """!
        @brief get printable string.

        @param indentation indentation.

        @returns printable string.
        """

        return ' ' * indentation + 'LayerDatabase\n'

class Emulator:
    """!
    @brief The Emulator class.

    Emulator class is the entry point for emulations. 
    """

    __registry: Registry
    __layers: LayerDatabase
    __dependencies_db: Dict[str, Set[Tuple[str, bool]]]
    __rendered: bool
    __bindings: BindingDatabase
    __resolved_bindings: Dict[str, core.Node]

    def __init__(self):
        """!
        @brief Construct a new emulation.
        """
        self.__rendered = False
        self.__dependencies_db = {}
        self.__resolved_bindings = {}
        self.__registry = Registry()
        self.__layers = LayerDatabase()
        self.__bindings = BindingDatabase()

        self.__registry.register('seedemu', 'dict', 'layersdb', self.__layers)
        self.__registry.register('seedemu', 'list', 'bindingdb', self.__bindings)

    def __render(self, layerName, optional: bool, configure: bool):
        """!
        @brief Render a layer.
        
        @param layerName name of layer.
        @throws AssertionError if dependencies unmet 
        """
        verb = 'configure' if configure else 'render'

        self.__log('requesting {}: {}'.format(verb, layerName))

        if optional and layerName not in self.__layers.db:
            self.__log('{}: not found but is optional, skipping'.format(layerName))
            return

        assert layerName in self.__layers.db, 'Layer {} requried but missing'.format(layerName)

        (layer, done) = self.__layers.db[layerName]
        if done:
            self.__log('{}: already done, skipping'.format(layerName))
            return

        if layerName in self.__dependencies_db:
            for (dep, opt) in self.__dependencies_db[layerName]:
                self.__log('{}: requesting dependency render: {}'.format(layerName, dep))
                self.__render(dep, opt, configure)

        self.__log('entering {}...'.format(layerName))

        hooks: List[core.Hook] = []
        for hook in self.__registry.getByType('seedemu', 'hook'):
            if hook.getTargetLayer() == layerName: hooks.append(hook)
        
        if configure:
            self.__log('invoking pre-configure hooks for {}...'.format(layerName))
            for hook in hooks: hook.preconfigure(self)
            self.__log('configureing {}...'.format(layerName))
            layer.configure(self)
            self.__log('invoking post-configure hooks for {}...'.format(layerName))
            for hook in hooks: hook.postconfigure(self)
        else:
            self.__log('invoking pre-render hooks for {}...'.format(layerName))
            for hook in hooks: hook.prerender(self)
            self.__log('rendering {}...'.format(layerName))
            layer.render(self)
            self.__log('invoking post-render hooks for {}...'.format(layerName))
            for hook in hooks: hook.postrender(self)
        
        self.__log('done: {}'.format(layerName))
        self.__layers.db[layerName] = (layer, True)
    
    def __loadDependencies(self, deps: Dict[str, Set[Tuple[str, bool]]]):
        """!
        @brief Load dependencies list.

        @param deps dependencies list.
        """
        for (layer, deps) in deps.items():
            if not layer in self.__dependencies_db:
                self.__dependencies_db[layer] = deps
                continue

            self.__dependencies_db[layer] |= deps

    def __log(self, message: str):
        """!
        @brief log to stderr.

        @param message message.
        """
        print('== Emulator: {}'.format(message), file=stderr)

    def rendered(self) -> bool:
        """!
        @brief test if the emulator is rendered.

        @returns True if rendered
        """
        return self.__rendered

    def addHook(self, hook: core.Hook):
        """!
        @brief Add a hook.

        @param hook Hook.
        """
        self.__registry.register('seedemu', 'hook', hook.getName(), hook)

    def addBinding(self, binding: core.Binding):
        """!
        @brief Add a binding.

        @param binding binding.
        """
        self.__bindings.db.append(binding)

    def getBindings(self) -> List[core.Binding]:
        """!
        @brief Get all bindings.

        @returns list of bindings.
        """
        return self.__bindings.db

    def addLayer(self, layer: core.Layer):
        """!
        @brief Add a layer.

        @param layer layer to add.
        @throws AssertionError if layer already exist.
        """

        lname = layer.getName()
        assert lname not in self.__layers.db, 'layer {} already added.'.format(lname)
        self.__registry.register('seedemu', 'layer', lname, layer)
        self.__layers.db[lname] = (layer, False)

    def getLayer(self, layerName: str) -> core.Layer:
        """!
        @brief Get a layer.

        @param layerName of the layer.
        @returns layer.
        """
        return self.__registry.get('seedemu', 'layer', layerName)

    def getLayers(self) -> List[core.Layer]:
        """!
        @brief Get all layers.

        @returns list of layers.
        """
        return self.__registry.getByType('seedemu', 'layer')

    def resolvVnode(self, vnode: str) -> core.Node:
        """!
        @brief resolve physical node for the given virtual node.

        @param vnode virtual node name.

        @returns physical node.
        """
        if vnode in self.__resolved_bindings: return self.__resolved_bindings[vnode]
        for binding in self.getBindings():
            pnode = binding.getCandidate(vnode, self.__registry, True)
            if pnode == None: continue
            return pnode
        assert False, 'cannot resolve vnode {}'.format(vnode)

    def getBindingFor(self, vnode: str) -> core.Node:
        """!
        @brief get physical node for the given virtual node from the
        pre-populated vnode-pnode mappings.

        Note that the bindings are processed in the early render stage, meaning
        calls to this function will always fail before render, and only virtual
        node names that have been used in service will be available to be
        "resolve" to the physical node using this function.

        This is meant to be used by services to find the physical node to
        install their servers on and should not be used for any other purpose. 
        if you try to resolve some arbitrary vnode names to physical node,
        use the resolveVnode function instead.

        tl;dr: don't use this, use resolvVnode, unless you know what you are
        doing.

        @param vnode virtual node.

        @returns physical node.
        """
        assert vnode in self.__resolved_bindings, 'failed to find binding for vnode {}.'.format(vnode)
        return self.__resolved_bindings[vnode]

    def render(self):
        """!
        @brief Render to emulation.

        @throws AssertionError if dependencies unmet 
        """
        assert not self.__rendered, 'already rendered.'

        for (layer, _) in self.__layers.db.values():
            self.__loadDependencies(layer.getDependencies())

        # render base first
        self.__render('Base', False, True)

        # collect all pending vnode names
        self.__log('collecting virtual node names in the emulation...')
        vnodes: List[str] = []
        for (layer, _) in self.__layers.db.values():
            if not isinstance(layer, core.Service): continue
            for (vnode, _) in layer.getPendingTargets().items():
                assert vnode not in vnodes, 'duplicated vnode: {}'.format(vnode)
                vnodes.append(vnode)
        self.__log('found {} virtual nodes.'.format(len(vnodes)))

        # resolv bindings for all vnodes
        self.__log('resolving binding for all virtual nodes...')
        for binding in self.getBindings():
            for vnode in vnodes:
                if vnode in self.__resolved_bindings: continue
                pnode = binding.getCandidate(vnode, self.__registry)
                if pnode == None: continue
                self.__log('vnode {} bound to as{}/{}'.format(vnode, pnode.getAsn(), pnode.getName()))
                self.__resolved_bindings[vnode] = pnode

        for layerName in self.__layers.db.keys():
            self.__render(layerName, False, True)

        # FIXME
        for (name, (layer, _)) in self.__layers.db.items():
            self.__layers.db[name] = (layer, False)

        for layerName in self.__layers.db.keys():
            self.__render(layerName, False, False)

        self.__rendered = True

    def compile(self, compiler: core.Compiler, output: str, override: bool = False):
        """!
        @brief Compile the simulation.

        @param compiler to use.
        @param output output directory path.
        @param override (optional) override the output folder if it already
        exist. False by defualt.
        """
        compiler.compile(self, output, override)

    def getRegistry(self) -> Registry: 
        """!
        @brief Get the Registry.

        @returns Registry.
        """
        return self.__registry

    def merge(self, other: Emulator, mergers: List[Merger] = [], vnodePrefix: str = '') -> Emulator:
        """!
        @brief merge two emulators.

        @param other the other emulator.
        @param mergers list of merge handlers.
        @param vnodePrefix prefix to add to the vnodes from the other emulator.

        @returns new emulator.
        """

        new_layers: Dict[Mergeable] = {}
        other_layers: Dict[Mergeable] = {}

        for l in self.getLayers(): new_layers[l.getTypeName()] = l
        for l in other.getLayers(): other_layers[l.getTypeName()] = l

        for l in other_layers.values():
            typename = l.getTypeName()

            if isinstance(l, core.Service):
                l.addPrefix(vnodePrefix)

            if typename not in new_layers.keys():
                new_layers[typename] = l
                continue

            merged = False

            for merger in mergers:
                if merger.getTargetType() != typename: continue
                new_layers[typename] = merger.doMerge(new_layers[typename], l)
                merged = True
            
            assert merged, 'abort: no merger found for {}'.format(typename)

        new_sim = Emulator()
        for l in new_layers.values(): new_sim.addLayer(l)

        for binding in self.getBindings(): new_sim.addBinding(binding)
        for binding in other.getBindings(): new_sim.addBinding(binding)

        return new_sim

    def dump(self, fileName: str):
        """!
        @brief dump the emulation to file.

        @param fileName output path.
        @throws AssertionError if the emulation is already rendered.
        """

        assert not self.__rendered, 'cannot dump emulation after render.'
        with open(fileName, 'wb') as f:
            pickle.dump(self.__registry, f)

    def load(self, fileName: str):
        """!
        @brief load emulation from file.

        @param fileName path to the dumped emulation.
        """

        with open(fileName, 'rb') as f:
            self.__rendered = False
            self.__dependencies_db = {}
            self.__registry = pickle.load(f)
            self.__layers = self.__registry.get('seedemu', 'dict', 'layersdb')
            self.__bindings = self.__registry.get('seedemu', 'list', 'bindingdb')