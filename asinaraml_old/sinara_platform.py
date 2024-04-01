from enum import Enum

class SinaraPlatform(Enum):
    Desktop = 'desktop'
    RemoteVM = 'remote_vm'

    def __str__(self):
        return self.value