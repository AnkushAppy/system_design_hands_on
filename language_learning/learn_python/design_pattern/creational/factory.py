from enum import StrEnum, auto
from typing import Protocol, Annotated, Literal, TypeAlias
from pydantic import BaseModel, Field, ConfigDict

# --- 1. The Domain Model (The "Product" structure) ---
# We use Pydantic to ensure the parsed DOM always follows a strict schema.

class DOMNode(BaseModel):
    model_config = ConfigDict(frozen=True) # Modern Pydantic V2 config
    
    tag: str
    attributes: dict[str, str] = Field(default_factory=dict)
    children: list["DOMNode"] = Field(default_factory=list)
    content: str | None = None

class DOMDocument(BaseModel):
    root: DOMNode
    version: str = "1.0"
    encoding: str = "UTF-8"

# --- 2. The Interface (The Protocol) ---
# In modern Python, Protocols (Static Duck Typing) are preferred over ABCs.

class XMLParser(Protocol):
    """Definition of the XML Parser interface."""
    def parse(self, xml_content: str) -> DOMDocument:
        ...

# --- 3. Concrete Implementations ---

class SaxonParser:
    """A high-performance parser implementation."""
    def parse(self, xml_content: str) -> DOMDocument:
        # Mock logic for Saxon parsing
        return DOMDocument(
            root=DOMNode(tag="root", content=f"Saxon parsed: {xml_content[:10]}...")
        )

class XalanParser:
    """An XSLT-heavy parser implementation."""
    def parse(self, xml_content: str) -> DOMDocument:
        # Mock logic for Xalan parsing
        return DOMDocument(
            root=DOMNode(tag="root", content=f"Xalan parsed: {xml_content[:10]}...")
        )

# --- 4. The Factory ---

class ParserType(StrEnum):
    SAXON = auto()
    XALAN = auto()

class ParserFactory:
    """The Factory responsible for instantiating the correct parser."""
    
    # We use a mapping for O(1) lookups, but Python 3.10+ match-case 
    # is also excellent for logic-heavy factories.
    _parsers: dict[ParserType, type[XMLParser]] = {
        ParserType.SAXON: SaxonParser,
        ParserType.XALAN: XalanParser,
    }

    @classmethod
    def create_parser(cls, method: ParserType) -> XMLParser:
        match method:
            case ParserType.SAXON:
                return SaxonParser()
            case ParserType.XALAN:
                return XalanParser()
            case _:
                raise ValueError(f"Unknown parser type: {method}")

# --- 5. Client Code ---

def main():
    # 1. Define the desired parser (e.g., from a config file or env var)
    selected_parser_type = ParserType.SAXON
    
    # 2. Use the factory to get the parser
    # The client doesn't care about the concrete class
    parser: XMLParser = ParserFactory.create_parser(selected_parser_type)
    
    # 3. Use the parser
    xml_data = "<note><body>Hello World</body></note>"
    dom: DOMDocument = parser.parse(xml_data)
    
    print(f"Used Parser: {type(parser).__name__}")
    print(f"DOM Content: {dom.root.content}")
    
    # Pydantic validation benefit:
    print(f"JSON Export: {dom.model_dump_json(indent=2)}")

if __name__ == "__main__":
    main()