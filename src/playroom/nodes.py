from collections.abc import Iterator, Sized
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class RecursiveNode(Sized):
    value: Optional[Any] = None
    left: Optional[RecursiveNode] = None
    right: Optional[RecursiveNode] = None

    def __str__(self, /):
        return f"({self.left} <- {self.value} -> {self.right})"

    def __len__(self, /):
        left_count = len(left) if (left := self.left) is not None else 0
        right_count = len(right) if (right := self.right) is not None else 0
        return left_count + right_count + 1

    def __iter__(self, /) -> Iterator[Any]:
        if left := self.left:
            yield from left
        yield self.value
        if right := self.right:
            yield from right

    def __reversed__(self, /) -> Iterator[Any]:
        if right := self.right:
            yield from reversed(right)
        yield self.value
        if left := self.left:
            yield from reversed(left)

    def height(self, /):
        left, right = self.left, self.right
        if left is right is None:
            return 0
        else:
            return max(len(left) if left else 0, len(right) if right else 0) + 1


a = RecursiveNode(
    100,
    RecursiveNode(50, RecursiveNode(25), RecursiveNode(75)),
    RecursiveNode(150, RecursiveNode(125), RecursiveNode(175)),
)

Node = RecursiveNode
print(a, len(a), a.height(), tuple(a), tuple(reversed(a)), sep="\n")
