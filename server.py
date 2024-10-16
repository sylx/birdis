import papermill as pm
from papermill.engines import NBClientEngine
from papermill.utils import remove_args, merge_kwargs
from nbformat import NotebookNode
from papermill.clientwrap import PapermillNotebookClient
from papermill.log import logger

class CustomEngine(NBClientEngine):
    client = None

    @classmethod
    def renumber_executions(cls, nb):
        for i, cell in enumerate(nb.cells):
            if 'execution_count' in cell:
                cell['execution_count'] = i + 1

    @classmethod
    def execute_managed_notebook(
            cls,
            nb_man,
            kernel_name,
            log_output=False,
            stdout_file=None,
            stderr_file=None,
            start_timeout=60,
            execution_timeout=None,
            **kwargs
    ):
        """
        Performs the actual execution of the parameterized notebook locally.

        Args:
            nb (NotebookNode): Executable notebook object.
            kernel_name (str): Name of kernel to execute the notebook against.
            log_output (bool): Flag for whether or not to write notebook output to the
                               configured logger.
            start_timeout (int): Duration to wait for kernel start-up.
            execution_timeout (int): Duration to wait before failing execution (default: never).
        """

        # Exclude parameters that named differently downstream
        safe_kwargs = remove_args(['timeout', 'startup_timeout'], **kwargs)

        # Nicely handle preprocessor arguments prioritizing values set by engine
        final_kwargs = merge_kwargs(
            safe_kwargs,
            timeout=execution_timeout if execution_timeout else kwargs.get('timeout'),
            startup_timeout=start_timeout,
            kernel_name=kernel_name,
            log=logger,
            log_output=log_output,
            stdout_file=stdout_file,
            stderr_file=stderr_file,
        )
        if not cls.client:
            cls.client = PapermillNotebookClient(nb_man, **final_kwargs)
        # accept new notebook into (possibly) existing client
        cls.client.nb_man = nb_man
        cls.client.nb = nb_man.nb
        # reuse client connection to existing kernel
        output = cls.client.execute(cleanup_kc=False)
        cls.renumber_executions(nb_man.nb)

        return output

# カスタムエンジンを登録
pm.engines.papermill_engines.register('custom_engine', CustomEngine)

#カスタムエンジンを使用してNotebookを実行
pm.execute_notebook(
    './PoC/windows_toasts.ipynb',
    './PoC/windows_toasts_output.ipynb',
    parameters=dict(x=0.6, y=0.1),
    engine_name='custom_engine'
)

# もう一度
pm.execute_notebook(
    './PoC/windows_toasts.ipynb',
    './PoC/windows_toasts_output.ipynb',
    parameters=dict(x=0.6, y=0.1),
    engine_name='custom_engine'
)