from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class TextAnnotation:
    locale: str = "en"
    description: str = ""


@dataclass(slots=True)
class DetectedLanguage:
    languageCode: str
    confidence: float


@dataclass(slots=True)
class Property:
    detectedLanguages: List[DetectedLanguage]


@dataclass(slots=True)
class Page:
    width: int
    height: int
    confidence: float
    property: Property | None = None


@dataclass(slots=True)
class FullTextAnnotation:
    pages: List[Page] = field(default_factory=list)
    text: str = ""

    @property
    def language_code(self) -> str:
        if not self.pages:
            return "auto"
        if not self.pages[0].property:
            return "auto"
        if not self.pages[0].property.detectedLanguages:
            return "auto"
        return self.pages[0].property.detectedLanguages[0].languageCode


@dataclass(slots=True)
class VisionError:
    code: int
    message: str


@dataclass(slots=True)
class VisionPayload:
    fullTextAnnotation: FullTextAnnotation
    textAnnotations: List[TextAnnotation] = field(default_factory=list)
    error: VisionError | None = None

    @property
    def text_value(self) -> str:
        return self.fullTextAnnotation.text or self.textAnnotations[0].description
