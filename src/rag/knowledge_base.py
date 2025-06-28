"""
Knowledge base management for RAG system
"""

import os
import json
from typing import List, Dict, Any, Optional
from loguru import logger
from src.config import settings


class KnowledgeBase:
    """Manages the knowledge base for RAG operations"""
    
    def __init__(self):
        self.data_path = "./data/knowledge"
        self.sources_file = os.path.join(self.data_path, "sources.json")
        self._ensure_data_directory()
        self.sources = self._load_sources()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_path, exist_ok=True)
        logger.info(f"Knowledge base directory: {self.data_path}")
    
    def _load_sources(self) -> Dict[str, Any]:
        """Load knowledge sources configuration"""
        if os.path.exists(self.sources_file):
            with open(self.sources_file, 'r') as f:
                return json.load(f)
        else:
            # Default sources
            default_sources = {
                "websites": [
                    {
                        "url": "https://kambocowboy.com",
                        "description": "Main Kambo information website",
                        "enabled": True
                    }
                ],
                "documents": [
                    {
                        "path": "./data/documents/kambo_faq.md",
                        "description": "Kambo FAQ document",
                        "enabled": True
                    }
                ],
                "research_papers": [
                    {
                        "title": "Kambo Research Overview",
                        "description": "Peer-reviewed research on Kambo",
                        "enabled": True
                    }
                ]
            }
            self._save_sources(default_sources)
            return default_sources
    
    def _save_sources(self, sources: Dict[str, Any]):
        """Save sources configuration"""
        with open(self.sources_file, 'w') as f:
            json.dump(sources, f, indent=2)
    
    def get_relevant_content(self, query: str) -> List[Dict[str, Any]]:
        """
        Get relevant content for a query
        This is a simplified version - in production, you'd use vector search
        """
        # Placeholder implementation
        relevant_content = [
            {
                "content": "Kambo is a traditional Amazonian medicine used in ceremonial contexts for purification and healing.",
                "source": "traditional_knowledge",
                "confidence": 0.9
            },
            {
                "content": "Kambo ceremonies should only be conducted by trained practitioners in safe environments.",
                "source": "safety_guidelines",
                "confidence": 0.95
            },
            {
                "content": "Research has shown potential benefits of Kambo in traditional healing practices, though more studies are needed.",
                "source": "research_papers",
                "confidence": 0.8
            }
        ]
        
        # Filter based on query relevance (simplified)
        query_lower = query.lower()
        filtered_content = []
        
        for item in relevant_content:
            if any(word in item["content"].lower() for word in query_lower.split()):
                filtered_content.append(item)
        
        return filtered_content[:3]  # Return top 3 results
    
    def add_source(self, source_type: str, source_data: Dict[str, Any]):
        """Add a new knowledge source"""
        if source_type not in self.sources:
            self.sources[source_type] = []
        
        self.sources[source_type].append(source_data)
        self._save_sources(self.sources)
        logger.info(f"Added new {source_type} source: {source_data.get('description', 'Unknown')}")
    
    def update_source(self, source_type: str, source_id: int, updates: Dict[str, Any]):
        """Update an existing knowledge source"""
        if source_type in self.sources and source_id < len(self.sources[source_type]):
            self.sources[source_type][source_id].update(updates)
            self._save_sources(self.sources)
            logger.info(f"Updated {source_type} source {source_id}") 