import logging
from plugins.boxplot import BoxplotPlugin
from plugins.scatter import ScatterPlugin
from plugins.volcano import VolcanoPlugin
from plugins.heatmap import HeatmapPlugin

logger = logging.getLogger(__name__)

class PluginDispatcher:
    """
    BioDiagnosis Plugin Dispatcher.
    Maps config keywords to Plugin Classes.
    """

    # 注册表：将用户可能的输入映射到类
    PLUGIN_MAP = {
        'box': BoxplotPlugin,
        'boxplot': BoxplotPlugin,
        'scatter': ScatterPlugin,
        'correlation': ScatterPlugin,
        'volcano': VolcanoPlugin, # [NEW]
        'heatmap': HeatmapPlugin  # [NEW]
    }

    def __init__(self, artifact_manager):
        self.am = artifact_manager

    def dispatch(self, config, df):
        """
        根据 config['graph'] 决定调用哪个插件
        """
        # 1. 提取图表类型 (默认 normalize 已经是小写了)
        graph_type = config.get('graph', '').lower()

        # 2. 默认 fallback 
        if not graph_type:
            logger.warning("No graph type specified. Defaulting to Boxplot.")
            graph_type = 'box'

        # 3. 查表分发
        plugins_cls = self.PLUGIN_MAP.get(graph_type)

        if not plugins_cls:
            valid_keys = list(self.PLUGIN_MAP.keys())
            raise ValueError(f"Unknown graph type: '{graph_type}'. Valid options: {valid_keys}")
        
        logger.info(f"Dispatcher: Selected plugin '{plugins_cls.__name__}' for graph '{graph_type}'")
        
        # 4. 实例化并运行插件生命周期
        # 这里的 run() 就是 base.py 里定义的 Template Method
        plugin = plugins_cls(self.am, config, df)
        plugin.run()
