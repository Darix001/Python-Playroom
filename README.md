A group of utilities usefull for writing better and faster python code. It focuses on writing more simpler and dry code, leaving the complexity in the backend rather than make the code complex. Below we'll give a few examples where this package may be usefull:

Note: This package was written in python 3.14.

Example #1: DRY

a common scenario in python, we have a custom class, with a group of private attributes, that we made public for access by properties,
but as we have more private attributes, the code becomes more and more repetitive:
```python
class Person:
    @property
    def name(self):
        return self._name
  
    @property
    def lastname(self):
        return self._lastname
  
    @property
    def gender(self):
        return self._gender
  
    @property
    def age(self):
        return self._age
  ```

Now let's see how the code looks with the methodtools.ReadOnlyPrivateDescriptor tool:
```python
class Person:
  name = lastname = gender = age = ReadOnlyPrivateDescriptor()
```

Wow!! that was a huge save of lines of code, from 16 to only 2 lines of code.

Example #2:
Every Experienced Python Programmer knows the itertools module. It is such an used and loved modules that there is a whole module dedicated to extend it's funcionality called the more_itertools. But sometimes, writing nested pipe with itertools.module makes the codeless readable. That's why people often just use sugar syntax like generators or list comprehesion. This is the pythonic way of writing generators, but sometimes you loss performance to gain more readability. With the iterpipe module in action, this is a concern of the past.

```python
from operator import methodcaller, attrgetter
  #Normal code with itertools and builtins
  with dir_objects as os.scandir('.'):
    ",".join(itertools.filterfalse(methodcaller("endswith", ".py"), map(attrgetter("name"), filter(methodcaller("is_file"), dir_objects))))
  
  #Generator version
  with dir_objects as os.scandir('.'):
    ",".join(obj.name for obj in dir_objects if obj.is_file() and obj.name.endswith(".py"))
  
  #Iterpipe version
  mutable_iterable = iterpipe.MutableIter()
  pipe = iterpipe.MutIter().method_filter('is_file').attr_map('name').method_filter('endswith', '.py')
  with dir_objects as os.scandir('.'):
      mutable_iterable.iterable = dir_objects
          ", ".join(pipe)
```
Not only is the later improves readability, but it also is much more faster than a generator or that a long itertools pipe that needs to be evaluated each time it is executed. And things just get better when you discover the iter_method_factory api in the iterpipe module.
