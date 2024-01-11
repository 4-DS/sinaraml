from enum import Enum

class SinaraInfra(Enum):
    LocalFileSystem = 'local_filesystem'

    def __str__(self):
        return self.value