#!/usr/bin/env python3
"""
Political Style Analyzer
========================

Analyze political communication styles and apply them to message generation.

Usage:
    python style_analyzer.py --analyze sample_speech.txt --politician "buttigieg"
    python style_analyzer.py --generate "Infrastructure Investment" --style buttigieg
"""

import argparse
import re
from typing import Dict, List, Tuple
from collections import Counter
import json

class PoliticalStyleAnalyzer:
    """Analyze and apply political communication styles."""
    
    def __init__(self):
        # Load style profiles from external JSON file
        try:
            with open("style_profiles.json", "r") as f:
                self.style_profiles = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load style_profiles.json: {e}")
            self.style_profiles = {}
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze text for style characteristics."""
        sentences = re.split(r'[.!?]+', text)
        words = re.findall(r'\b\w+\b', text.lower())
        
        analysis = {
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "avg_sentence_length": len(words) / max(len(sentences), 1),
            "vocabulary_richness": len(set(words)) / len(words) if words else 0,
            "frequent_words": Counter(words).most_common(10),
            "style_indicators": {}
        }
        
        # Analyze against known styles
        for politician, profile in self.style_profiles.items():
            score = 0
            found_keywords = []
            
            for keyword in profile["keywords"]:
                if keyword.lower() in text.lower():
                    score += 1
                    found_keywords.append(keyword)
            
            analysis["style_indicators"][politician] = {
                "score": score,
                "percentage": (score / len(profile["keywords"])) * 100,
                "found_keywords": found_keywords
            }
        
        return analysis
    
    def generate_styled_message(self, topic: str, style: str, length: str = "medium") -> str:
        """Generate a message in a specific political style."""
        if style not in self.style_profiles:
            return f"Style '{style}' not available. Available: {list(self.style_profiles.keys())}"
        
        profile = self.style_profiles[style]
        
        # Select appropriate pattern
        patterns = profile["sentence_patterns"]
        
        if style == "buttigieg":
            return self._generate_buttigieg_style(topic, profile, length)
        elif style == "obama":
            return self._generate_obama_style(topic, profile, length)
        else:
            return f"Generation for {style} style not yet implemented"
    
    def _generate_buttigieg_style(self, topic: str, profile: Dict, length: str) -> str:
        """Generate message in Buttigieg's style."""
        
        # Core message structure
        messages = []
        
        # Opening - practical framing
        opening = f"When we talk about {topic}, we're talking about something that touches every community in America."
        messages.append(opening)
        
        # Policy connection
        policy = f"That's why our investments in {topic} aren't just policy choices - they're investments in working families and the communities they call home."
        messages.append(policy)
        
        # Future vision
        if length in ["medium", "long"]:
            vision = f"We can build a future where every American has access to the opportunities that {topic} creates."
            messages.append(vision)
        
        # Call to action
        if length == "long":
            action = f"This is about more than {topic} - it's about the values we share and the future we're building together."
            messages.append(action)
        
        return " ".join(messages)
    
    def _generate_obama_style(self, topic: str, profile: Dict, length: str) -> str:
        """Generate message in Obama's style."""
        messages = []
        
        # Inspirational opening
        opening = f"We know that {topic} represents more than just an issue - it represents our hopes for the future."
        messages.append(opening)
        
        # Unity theme
        unity = f"When we come together around {topic}, we show what's possible when we choose hope over fear."
        messages.append(unity)
        
        if length in ["medium", "long"]:
            call = f"This is our moment to act on {topic} - not for ourselves, but for the generations that will follow."
            messages.append(call)
        
        return " ".join(messages)
    
    def extract_style_from_file(self, filepath: str) -> Dict:
        """Extract style characteristics from a text file."""
        try:
            with open(filepath, 'r') as f:
                text = f.read()
            return self.analyze_text(text)
        except FileNotFoundError:
            return {"error": f"File {filepath} not found"}
    
    def compare_styles(self, text1: str, text2: str) -> Dict:
        """Compare the styles of two texts."""
        analysis1 = self.analyze_text(text1)
        analysis2 = self.analyze_text(text2)
        
        comparison = {
            "text1_analysis": analysis1,
            "text2_analysis": analysis2,
            "differences": {
                "avg_sentence_length": abs(analysis1["avg_sentence_length"] - analysis2["avg_sentence_length"]),
                "vocabulary_richness": abs(analysis1["vocabulary_richness"] - analysis2["vocabulary_richness"])
            }
        }
        
        return comparison

def main():
    """Main CLI function for style analysis."""
    
    parser = argparse.ArgumentParser(
        description="Analyze and generate political communication styles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --analyze speech.txt --politician buttigieg
    %(prog)s --generate "Climate Change" --style buttigieg --length medium
    %(prog)s --compare file1.txt file2.txt
        """
    )
    
    parser.add_argument("--analyze", help="Analyze text file for style characteristics")
    parser.add_argument("--politician", help="Compare against specific politician's style")
    parser.add_argument("--generate", help="Generate message for topic")
    parser.add_argument("--style", choices=["buttigieg", "obama"], 
                       help="Political style to emulate")
    parser.add_argument("--length", choices=["short", "medium", "long"], 
                       default="medium", help="Message length")
    parser.add_argument("--compare", nargs=2, help="Compare styles of two files")
    parser.add_argument("--export", help="Export analysis to JSON file")
    
    args = parser.parse_args()
    
    analyzer = PoliticalStyleAnalyzer()
    
    if args.analyze:
        analysis = analyzer.extract_style_from_file(args.analyze)
        
        if "error" in analysis:
            print(f"❌ {analysis['error']}")
            return
        
        print("=" * 60)
        print(f"STYLE ANALYSIS: {args.analyze}")
        print("=" * 60)
        
        print(f"\n📊 BASIC METRICS")
        print(f"Word count: {analysis['word_count']}")
        print(f"Sentences: {analysis['sentence_count']}")
        print(f"Avg sentence length: {analysis['avg_sentence_length']:.1f} words")
        print(f"Vocabulary richness: {analysis['vocabulary_richness']:.2f}")
        
        print(f"\n🎯 STYLE MATCHING")
        for politician, indicators in analysis["style_indicators"].items():
            print(f"{politician.title()}: {indicators['percentage']:.1f}% match")
            if indicators['found_keywords']:
                print(f"  Keywords: {', '.join(indicators['found_keywords'][:5])}")
        
        if args.export:
            with open(args.export, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"\n✅ Analysis exported to {args.export}")
    
    elif args.generate and args.style:
        message = analyzer.generate_styled_message(args.generate, args.style, args.length)
        
        print("=" * 60)
        print(f"GENERATED MESSAGE ({args.style.upper()} STYLE)")
        print("=" * 60)
        print(f"Topic: {args.generate}")
        print(f"Length: {args.length}")
        print()
        print(message)
        print()
        
        # Quick analysis of generated message
        analysis = analyzer.analyze_text(message)
        print(f"📊 Generated message stats:")
        print(f"Words: {analysis['word_count']}")
        print(f"Style match: {analysis['style_indicators'][args.style]['percentage']:.1f}%")
    
    elif args.compare:
        comparison = analyzer.compare_styles(
            open(args.compare[0]).read(),
            open(args.compare[1]).read()
        )
        
        print("=" * 60)
        print(f"STYLE COMPARISON")
        print("=" * 60)
        print(f"File 1: {args.compare[0]}")
        print(f"File 2: {args.compare[1]}")
        print()
        
        print("Sentence length difference:", 
              f"{comparison['differences']['avg_sentence_length']:.1f} words")
        print("Vocabulary richness difference:", 
              f"{comparison['differences']['vocabulary_richness']:.3f}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()