"""The port an implementation writes to claim Datum conformance.

Subclass DatumAdapter, implement what you support, and run:

    python3 -m conformance.runner.run --adapter yourmodule:YourAdapter

Unimplemented methods raise NotImplementedError, which the runner reports as a
level failure rather than a crash. Partial implementations are expected and are
scored honestly — that is the point of scoring per level rather than in
aggregate.
"""

from abc import ABC, abstractmethod


class NotSupported(NotImplementedError):
    """Raised by an adapter for a tool it does not implement."""


class DatumAdapter(ABC):
    """Four tools, plus merge, plus fixture loading.

    Every method receives the raw `args` object from the vector and the calling
    principal. Return the tool's response as a plain dict — the runner asserts
    against it directly, so the shape you return is the shape you are claiming
    conformance for.
    """

    name = "unnamed"

    @abstractmethod
    def load_fixture(self, fixture):
        """Reset to the given canon state.

        Called before every vector. `fixture` carries nodes, claims, commits,
        branches, and optionally edges, constraints, and imports.
        """

    def read(self, args, principal):
        raise NotSupported("datum.read")

    def check(self, args, principal):
        raise NotSupported("datum.check")

    def propose(self, args, principal):
        raise NotSupported("datum.propose")

    def commit(self, args, principal):
        raise NotSupported("datum.commit")

    def merge(self, args, principal):
        raise NotSupported("datum.merge")

    def dispatch(self, tool, args, principal):
        return {
            "datum.read": self.read,
            "datum.check": self.check,
            "datum.propose": self.propose,
            "datum.commit": self.commit,
            "datum.merge": self.merge,
        }[tool](args, principal)
