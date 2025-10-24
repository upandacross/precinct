#!/usr/bin/env python3
"""
Message Text Generator CLI
==========================

A standalone command-line tool for generating text messages with specified subject and length.

Usage:
    python message_generator_cli.py "voter outreach" short --tone formal
    python message_generator_cli.py "fundraising event" custom --words 250 --tone persuasive
    python message_generator_cli.py "meeting reminder" medium --format email
"""

import argparse
import sys
import textwrap
from typing import Dict, Any

def generate_message_content(subject: str, length: str, **kwargs) -> str:
    """
    Generate message content based on parameters.
    
    Args:
        subject: The main topic/subject of the message
        length: short/medium/long/custom
        **kwargs: Additional parameters like tone, format, word_count, etc.
    
    Returns:
        Generated message text
    """
    # Length mapping
    length_map = {
        "short": 50,
        "medium": 150,
        "long": 300,
        "custom": kwargs.get("word_count", 150)
    }
    
    target_words = length_map.get(length, 150)
    tone = kwargs.get("tone", "informative")
    format_type = kwargs.get("format", "general")
    audience = kwargs.get("audience", "general")
    
    # Message templates based on format
    templates = {
        "email": {
            "structure": ["subject_line", "greeting", "body", "call_to_action", "closing"],
            "greeting": "Dear [Recipient]," if tone == "formal" else "Hello!",
            "closing": "Best regards," if tone == "formal" else "Thanks!"
        },
        "sms": {
            "structure": ["body", "call_to_action"],
            "max_chars": 160
        },
        "social_media": {
            "structure": ["hook", "body", "hashtags"],
            "max_chars": 280
        },
        "letter": {
            "structure": ["date", "greeting", "body", "call_to_action", "closing"],
            "greeting": "Dear [Recipient]," if tone == "formal" else "Hello!",
            "closing": "Sincerely," if tone == "formal" else "Best,"
        },
        "general": {
            "structure": ["body", "call_to_action"]
        }
    }
    
    # Content generation based on tone and subject
    import json
    import os
    content_generators = {
        "formal": generate_formal_content,
        "casual": generate_casual_content,
        "persuasive": generate_persuasive_content,
        "informative": generate_informative_content,
        "urgent": generate_urgent_content
    }
    # Dynamically add political styles from style_profiles.json
    style_profiles_path = os.path.join(os.path.dirname(__file__), "style_profiles.json")
    try:
        with open(style_profiles_path, "r") as f:
            style_profiles = json.load(f)
        for style_name in style_profiles:
            if style_name not in content_generators:
                # Use a generic generator for new styles
                def make_style_gen(style):
                    def gen(subject, word_count, template, context):
                        opening = f"[{style.title()} Style] {subject}: "
                        body = f"This message is generated using the {style} style profile."
                        return f"{opening}\n{body}"
                    return gen
                content_generators[style_name] = make_style_gen(style_name)
    except Exception as e:
        pass
    generator = content_generators.get(tone, generate_informative_content)
    template = templates.get(format_type, templates["general"])
    
    # Create context dict for generator
    context = {
        "tone": tone,
        "format_type": format_type,
        "audience": audience,
        **kwargs
    }
    
    return generator(subject, target_words, template, context)

def generate_formal_content(subject: str, word_count: int, template: Dict, context: Dict) -> str:
    """Generate formal tone content."""
    intro_phrases = [
        "I am writing to inform you about",
        "Please be advised regarding",
        "This communication concerns",
        "I would like to bring to your attention"
    ]
    
    body_starters = [
        "The purpose of this message is to",
        "We are pleased to announce",
        "It is important to note that",
        "Please be aware that"
    ]
    
    # Generate structured content
    parts = []
    
    if "greeting" in template.get("structure", []):
        parts.append(template["greeting"])
        parts.append("")
    
    # Main content
    intro = f"{intro_phrases[hash(subject) % len(intro_phrases)]} {subject}."
    parts.append(intro)
    parts.append("")
    
    body = f"{body_starters[hash(subject) % len(body_starters)]} provide you with comprehensive information regarding {subject}. This matter requires your attention and consideration."
    
    # Expand body to meet word count
    if word_count > 100:
        body += f" We believe that {subject} represents an important opportunity for positive impact. Your participation and engagement would be greatly valued in this initiative."
    
    if word_count > 200:
        body += f" Please review the details carefully and consider how {subject} aligns with your interests and availability. We are committed to ensuring all stakeholders are properly informed."
    
    parts.append(body)
    parts.append("")
    
    if "call_to_action" in template.get("structure", []):
        cta = "Please do not hesitate to contact us if you require additional information or have any questions regarding this matter."
        parts.append(cta)
        parts.append("")
    
    if "closing" in template.get("structure", []):
        parts.append(template["closing"])
    
    return "\n".join(parts)

def generate_casual_content(subject: str, word_count: int, template: Dict, context: Dict) -> str:
    """Generate casual tone content."""
    intro_phrases = [
        "Hey! Just wanted to let you know about",
        "Quick update on",
        "Thought you'd be interested in",
        "Wanted to share some news about"
    ]
    
    parts = []
    
    if "greeting" in template.get("structure", []):
        parts.append("Hey there!")
        parts.append("")
    
    intro = f"{intro_phrases[hash(subject) % len(intro_phrases)]} {subject}!"
    parts.append(intro)
    parts.append("")
    
    body = f"So here's the deal with {subject} - it's pretty exciting stuff. I think you'll find it interesting and worth checking out."
    
    if word_count > 100:
        body += f" The whole {subject} thing has been getting a lot of attention lately, and for good reason. It's definitely something that could make a real difference."
    
    if word_count > 200:
        body += f" I've been following {subject} for a while now and I'm really impressed with how it's developing. The community response has been amazing and there's so much potential here."
    
    parts.append(body)
    parts.append("")
    
    if "call_to_action" in template.get("structure", []):
        cta = "Let me know what you think! Would love to hear your thoughts on this."
        parts.append(cta)
        parts.append("")
    
    if "closing" in template.get("structure", []):
        parts.append("Talk soon!")
    
    return "\n".join(parts)

def generate_persuasive_content(subject: str, word_count: int, template: Dict, context: Dict) -> str:
    """Generate persuasive tone content."""
    hook_phrases = [
        "Imagine the impact we could make with",
        "Don't miss this opportunity to be part of",
        "Your support could be the key to",
        "Together, we can transform"
    ]
    
    parts = []
    
    if "greeting" in template.get("structure", []):
        parts.append("Dear Friend,")
        parts.append("")
    
    hook = f"{hook_phrases[hash(subject) % len(hook_phrases)]} {subject}."
    parts.append(hook)
    parts.append("")
    
    body = f"Right now, {subject} needs champions like you. Your involvement isn't just helpful - it's essential for success."
    
    if word_count > 100:
        body += f" Every day we wait, opportunities slip away. But with your support, {subject} can achieve remarkable results that benefit everyone involved."
    
    if word_count > 200:
        body += f" History shows us that real change happens when committed individuals unite behind important causes. {subject} represents exactly that kind of opportunity - a chance to make a lasting difference."
    
    parts.append(body)
    parts.append("")
    
    if "call_to_action" in template.get("structure", []):
        cta = f"Will you join us in supporting {subject}? Your participation today can create the change we need tomorrow."
        parts.append(cta)
        parts.append("")
    
    if "closing" in template.get("structure", []):
        parts.append("Together we can make a difference,")
    
    return "\n".join(parts)

def generate_informative_content(subject: str, word_count: int, template: Dict, context: Dict) -> str:
    """Generate informative tone content."""
    parts = []
    
    if "greeting" in template.get("structure", []):
        parts.append("Hello,")
        parts.append("")
    
    intro = f"This message provides important information about {subject}."
    parts.append(intro)
    parts.append("")
    
    body = f"Understanding {subject} is crucial for making informed decisions. Here's what you need to know: {subject} involves multiple factors that impact our community and requires careful consideration."
    
    if word_count > 100:
        body += f" Recent developments in {subject} have highlighted several key points that deserve attention. These include both opportunities and challenges that need to be addressed."
    
    if word_count > 200:
        body += f" Research and analysis of {subject} reveal complex dynamics that affect various stakeholders. By staying informed about these developments, we can better prepare for future changes and make strategic decisions."
    
    parts.append(body)
    parts.append("")
    
    if "call_to_action" in template.get("structure", []):
        cta = f"For more information about {subject}, please don't hesitate to reach out with any questions."
        parts.append(cta)
        parts.append("")
    
    if "closing" in template.get("structure", []):
        parts.append("Best regards,")
    
    return "\n".join(parts)

def generate_urgent_content(subject: str, word_count: int, template: Dict, context: Dict) -> str:
    """Generate urgent tone content."""
    urgent_phrases = [
        "URGENT:",
        "TIME-SENSITIVE:",
        "IMMEDIATE ACTION NEEDED:",
        "BREAKING:"
    ]
    
    parts = []
    
    urgent_marker = f"{urgent_phrases[hash(subject) % len(urgent_phrases)]} {subject}"
    parts.append(urgent_marker)
    parts.append("")
    
    body = f"This is a time-sensitive matter regarding {subject}. Immediate attention is required to address this situation effectively."
    
    if word_count > 100:
        body += f" The deadline for {subject} is approaching rapidly. Delays could result in missed opportunities or negative consequences."
    
    if word_count > 200:
        body += f" We have limited time to respond to {subject} properly. Your quick action and support are critical for achieving the best possible outcome."
    
    parts.append(body)
    parts.append("")
    
    cta = f"Please respond regarding {subject} as soon as possible. Time is of the essence."
    parts.append(cta)
    
    return "\n".join(parts)

def generate_buttigieg_content(subject: str, word_count: int, template: Dict, context: Dict) -> str:
    """Generate content in Pete Buttigieg's style."""
    parts = []
    
    # Opening with community focus
    opening = f"When we talk about {subject}, we're talking about something that touches every community in America."
    parts.append(opening)
    parts.append("")
    
    # Policy connection to families
    body = f"That's why our work on {subject} isn't just about policy - it's about investing in working families and the communities they call home."
    
    # Add content based on word count
    if word_count > 100:
        body += f" We can build a future where every American has access to the opportunities that {subject} creates."
        if word_count > 150:
            body += f" This is about more than {subject} - it's about the values we share and the future we're building together."
    
    parts.append(body)
    parts.append("")
    
    # Call to action with practical focus
    cta = f"Let's work together to make progress on {subject} for all Americans."
    parts.append(cta)
    
    return "\n".join(parts)

def generate_obama_content(subject: str, word_count: int, template: Dict, context: Dict) -> str:
    """Generate content in Barack Obama's style."""
    parts = []
    
    # Inspirational opening
    opening = f"We know that {subject} represents more than just an issue - it represents our hopes for the future."
    parts.append(opening)
    parts.append("")
    
    # Unity and hope theme
    body = f"When we come together around {subject}, we show what's possible when we choose hope over fear."
    
    # Add content based on word count  
    if word_count > 100:
        body += f" This is our moment to act on {subject} - not for ourselves, but for the generations that will follow."
        if word_count > 150:
            body += f" Because when we stand up for {subject}, we're standing up for the America we believe in."
    
    parts.append(body)
    parts.append("")
    
    # Inspirational call to action
    cta = f"Together, we can make {subject} a reality for everyone."
    parts.append(cta)
    
    return "\n".join(parts)

def word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Generate text messages with specified subject and length",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
            %(prog)s "voter outreach campaign" short --tone formal
            %(prog)s "fundraising event" custom --words 250 --tone persuasive --format email
            %(prog)s "meeting reminder" medium --format sms --tone casual
            %(prog)s "policy update" long --tone informative --audience technical
        """)
    )
    
    parser.add_argument("subject", help="Subject/topic for the message")
    parser.add_argument("length", choices=["short", "medium", "long", "custom"],
                       help="Message length (short=~50 words, medium=~150, long=~300)")
    
    parser.add_argument("--words", type=int, default=150,
                       help="Specific word count (used with custom length)")
    # Dynamically load style choices
    import json
    import os
    style_choices = ["formal", "casual", "persuasive", "informative", "urgent"]
    style_profiles_path = os.path.join(os.path.dirname(__file__), "style_profiles.json")
    try:
        with open(style_profiles_path, "r") as f:
            style_profiles = json.load(f)
        style_choices += list(style_profiles.keys())
    except Exception:
        pass
    parser.add_argument("--tone", choices=style_choices,
                       default="informative", help="Tone of the message or political style")
    parser.add_argument("--format", choices=["email", "sms", "social_media", "letter", "general"],
                       default="general", help="Message format/platform")
    parser.add_argument("--audience", choices=["general", "technical", "executive", "youth", "seniors"],
                       default="general", help="Target audience")
    parser.add_argument("--show-stats", action="store_true",
                       help="Show word count and character count statistics")
    
    args = parser.parse_args()
    
    # Generate message
    try:
        message = generate_message_content(
            subject=args.subject,
            length=args.length,
            word_count=args.words,
            tone=args.tone,
            format=args.format,
            audience=args.audience
        )
        
        print("=" * 60)
        print(f"Generated Message: {args.tone.title()} tone about '{args.subject}'")
        print("=" * 60)
        print()
        print(message)
        print()
        
        if args.show_stats:
            words = word_count(message)
            chars = len(message)
            print("-" * 40)
            print(f"Statistics:")
            print(f"  Word count: {words}")
            print(f"  Character count: {chars}")
            print(f"  Target was: {args.words if args.length == 'custom' else {'short': 50, 'medium': 150, 'long': 300}[args.length]} words")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error generating message: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()