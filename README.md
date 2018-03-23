# Arcutil

Arcutil is  series of helpful utility functions and scripts that are designed to augment Esri's ArcGIS software.

## How to use arcutil

Until this project becomes more structured the easiest way to import any functions in this library is to use `sys.path.append()` to append the arcutil subdirectory to your system path and then you can import any modules or functions desired.

For example:

```python
import sys
sys.path.append(r'C:/<Users>/<Username>/Github/Arcutil/arcutil')
import utilities as util
import arcpy_utilities as arcutil
from context import *

#The rest of your code...
```
