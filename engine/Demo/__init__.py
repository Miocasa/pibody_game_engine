class _Demo():
    def run(self):
        from .main import Demo
        Demo().run()
demo = _Demo()