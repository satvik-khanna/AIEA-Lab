import re
from typing import Dict, Any
import os
import json

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

os.environ["OPENAI_API_KEY"] = "x"

class KnowledgeBase:
    def __init__(self):
        self.facts = [
            ("father", "john", "alice"),
            ("father", "john", "bob"),
            ("father", "mike", "john"),
            ("father", "peter", "lucy"),
            ("father", "james", "peter"),
            ("father", "david", "sarah"),
            ("father", "eric", "tom"),
            ("father", "tom", "emma"),
            ("mother", "mary", "alice"),
            ("mother", "mary", "bob"),
            ("mother", "sarah", "john"),
            ("mother", "jennifer", "lucy"),
            ("mother", "patricia", "peter"),
            ("mother", "laura", "sarah"),
            ("mother", "karen", "tom"),
            ("mother", "lisa", "emma"),
        ]
        
    def query(self, predicate, args):
        results = []
        var_positions = [i for i, arg in enumerate(args) if isinstance(arg, Var)]
        for fact in self.facts:
            if fact[0] == predicate:
                match = True
                for i, arg in enumerate(args):
                    if i + 1 < len(fact) and not isinstance(arg, Var) and arg != fact[i + 1]:
                        match = False
                        break
                if match:
                    result = {}
                    for pos in var_positions:
                        if pos + 1 < len(fact):
                            var_name = args[pos].name
                            result[var_name] = fact[pos + 1]
                    if result or not var_positions:
                        results.append(result)
        return results
    
    def query_rule(self, rule_name, args):
        if rule_name == "is_father":
            return self.query("father", args)
        elif rule_name == "is_mother":
            return self.query("mother", args)
        elif rule_name == "is_parent":
            father_results = self.query("father", args)
            mother_results = self.query("mother", args)
            return father_results + mother_results
        elif rule_name == "is_child":
            swapped_args = [args[1], args[0]] if len(args) >= 2 else args
            return self.query_rule("is_parent", swapped_args)
        elif rule_name == "is_grandparent":
            results = []
            child_arg = args[1] if len(args) >= 2 else None
            if not isinstance(args[0], Var):
                potential_parent = Var("Y")
                parent_results = self.query_rule("is_child", [potential_parent, args[0]])
                for parent_result in parent_results:
                    parent_name = parent_result.get("Y")
                    if parent_name:
                        if self.query_rule("is_parent", [parent_name, child_arg]):
                            results.append({})
                return results
            parent_var = Var("Y")
            parent_results = self.query_rule("is_parent", [parent_var, child_arg])
            for parent_result in parent_results:
                parent_name = parent_result.get("Y")
                if parent_name:
                    grandparent_results = self.query_rule("is_parent", [Var("X"), parent_name])
                    results.extend(grandparent_results)
            return results
        elif rule_name == "is_sibling":
            results = []
            if len(args) >= 2 and not isinstance(args[0], Var) and not isinstance(args[1], Var):
                person1, person2 = args[0], args[1]
                parent_var = Var("Z")
                parents1 = self.query_rule("is_parent", [parent_var, person1])
                for parent_result in parents1:
                    parent_name = parent_result.get("Z")
                    if parent_name:
                        if self.query_rule("is_parent", [parent_name, person2]):
                            if person1 != person2:
                                return [{}]
                return []
            if len(args) >= 2 and isinstance(args[0], Var):
                person = args[1]
                parent_var = Var("Z")
                parents = self.query_rule("is_parent", [parent_var, person])
                for parent_result in parents:
                    parent_name = parent_result.get("Z")
                    if parent_name:
                        potential_siblings = self.query_rule("is_child", [Var("X"), parent_name])
                        for sibling_result in potential_siblings:
                            sibling_name = sibling_result.get("X")
                            if sibling_name and sibling_name != person:
                                results.append({"X": sibling_name})
            unique_results = []
            seen = set()
            for result in results:
                if "X" in result and result["X"] not in seen:
                    seen.add(result["X"])
                    unique_results.append(result)
            return unique_results
        return []

class Var:
    def __init__(self, name):
        self.name = name
        self.value = None
    def __repr__(self):
        return f"_{self.name}"

class ProblemFormulator:
    def __init__(self):
        self.templates = [
            {
                "pattern": r"Who is the father of (\w+)\?",
                "predicate": "is_father",
                "args": [lambda m: Var("X"), lambda m: m.group(1).lower()]
            },
            {
                "pattern": r"Is (\w+) the father of (\w+)\?",
                "predicate": "is_father",
                "args": [lambda m: m.group(1).lower(), lambda m: m.group(2).lower()]
            },
            {
                "pattern": r"Who is the mother of (\w+)\?",
                "predicate": "is_mother",
                "args": [lambda m: Var("X"), lambda m: m.group(1).lower()]
            },
            {
                "pattern": r"Is (\w+) the mother of (\w+)\?",
                "predicate": "is_mother",
                "args": [lambda m: m.group(1).lower(), lambda m: m.group(2).lower()]
            },
            {
                "pattern": r"Who (are|is) the (children|child) of (\w+)\?",
                "predicate": "is_child",
                "args": [lambda m: Var("X"), lambda m: m.group(3).lower()]
            },
            {
                "pattern": r"Is (\w+) a child of (\w+)\?",
                "predicate": "is_child",
                "args": [lambda m: m.group(1).lower(), lambda m: m.group(2).lower()]
            },
            {
                "pattern": r"Who (are|is) the grandparent(s)? of (\w+)\?",
                "predicate": "is_grandparent",
                "args": [lambda m: Var("X"), lambda m: m.group(3).lower()]
            },
            {
                "pattern": r"Is (\w+) a grandparent of (\w+)\?",
                "predicate": "is_grandparent",
                "args": [lambda m: m.group(1).lower(), lambda m: m.group(2).lower()]
            },
            {
                "pattern": r"Who (are|is) the sibling(s)? of (\w+)\?",
                "predicate": "is_sibling",
                "args": [lambda m: Var("X"), lambda m: m.group(3).lower()]
            },
            {
                "pattern": r"Are (\w+) and (\w+) siblings\?",
                "predicate": "is_sibling",
                "args": [lambda m: m.group(1).lower(), lambda m: m.group(2).lower()]
            }
        ]
    
    def formulate(self, question: str) -> Dict[str, Any]:
        for template in self.templates:
            match = re.match(template["pattern"], question, re.IGNORECASE)
            if match:
                args = [arg_extractor(match) for arg_extractor in template["args"]]
                formulation = {
                    "predicate": template["predicate"],
                    "args": args,
                    "query_type": "boolean" if all(not isinstance(arg, Var) for arg in args) else "wh-question",
                    "original_question": question
                }
                return formulation
        return {
            "predicate": None,
            "args": [],
            "query_type": None,
            "original_question": question
        }

class SymbolicReasoner:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
    def reason(self, formulation: Dict[str, Any]) -> List[Dict[str, str]]:
        predicate = formulation.get("predicate")
        args = formulation.get("args", [])
        if not predicate or not args:
            return []
        return self.kb.query_rule(predicate, args)

class ResultInterpreter:
    def interpret(self, reasoning_results: List[Dict[str, str]], formulation: Dict[str, Any]) -> str:
        if not reasoning_results:
            predicate = formulation.get("predicate", "")
            args = formulation.get("args", [])
            query_type = formulation.get("query_type", "")
            if query_type == "boolean":
                rel_type = predicate.replace("is_", "")
                return f"No, {args[0]} is not the {rel_type} of {args[1]} based on the available information."
            else:
                rel_type = predicate.replace("is_", "")
                return f"I couldn't find any {rel_type}s of {args[1]} based on the available information."
        predicate = formulation.get("predicate", "").replace("is_", "")
        args = formulation.get("args", [])
        query_type = formulation.get("query_type", "")
        if query_type == "boolean":
            return f"Yes, {args[0]} is the {predicate} of {args[1]}."
        responses = []
        for result in reasoning_results:
            var_arg_index = None
            for i, arg in enumerate(args):
                if isinstance(arg, Var):
                    var_arg_index = i
                    break
            if var_arg_index is not None and result:
                var_name = args[var_arg_index].name
                if var_name in result:
                    value = result[var_name]
                    if predicate == "father":
                        responses.append(f"{value} is the father of {args[1]}.")
                    elif predicate == "mother":
                        responses.append(f"{value} is the mother of {args[1]}.")
                    elif predicate == "child":
                        responses.append(f"{value} is a child of {args[1]}.")
                    elif predicate == "grandparent":
                        responses.append(f"{value} is a grandparent of {args[1]}.")
                    elif predicate == "sibling":
                        responses.append(f"{value} is a sibling of {args[1]}.")
        if responses:
            return "\n".join(responses)
        else:
            return "No specific results found based on the available information."

class SimpleRAG:
    def __init__(self):
        self.knowledge = [
            "John is the father of Alice and Bob.",
            "Mary is the mother of Alice and Bob.",
            "Mike is John's father, making him Alice and Bob's grandfather.",
            "Sarah is John's mother, making her Alice and Bob's grandmother.",
            "Peter is Lucy's father.",
            "Jennifer is Lucy's mother.",
            "James is Peter's father, making him Lucy's grandfather.",
            "Patricia is Peter's mother, making her Lucy's grandmother.",
            "Alice and Bob are siblings because they share the same parents (John and Mary).",
            "Family relationships include parents (mother and father), children, siblings, and grandparents.",
            "David is Sarah's father.",
            "Laura is Sarah's mother.",
            "Eric is Tom's father.",
            "Karen is Tom's mother.",
            "Tom is Emma's father.",
            "Lisa is Emma's mother."
        ]
    
    def query(self, question: str) -> str:
        question_lower = question.lower()
        relevant_entries = []
        entities = re.findall(r'\b([a-z]+)\b', question_lower)
        relevant_entities = [entity for entity in entities if len(entity) > 3 and entity not in ["what", "who", "where", "when", "tell", "about", "family", "relationship"]]
        for entity in relevant_entities:
            for entry in self.knowledge:
                if entity in entry.lower():
                    relevant_entries.append(entry)
        if relevant_entries:
            return "Based on my knowledge: " + " ".join(relevant_entries)
        else:
            return "I don't have specific information about that relationship in my knowledge base."

class LogicLM:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.problem_formulator = ProblemFormulator()
        self.symbolic_reasoner = SymbolicReasoner(self.kb)
        self.result_interpreter = ResultInterpreter()
        self.simple_rag = SimpleRAG()
    
    def answer_question(self, question: str) -> str:
        formulation = self.problem_formulator.formulate(question)
        if not formulation.get("predicate"):
            return self.simple_rag.query(question)
        reasoning_results = self.symbolic_reasoner.reason(formulation)
        answer = self.result_interpreter.interpret(reasoning_results, formulation)
        return answer

if __name__ == "__main__":
    logic_lm = LogicLM()
    questions = [
        "Who is the father of alice?",
        "Is john the father of bob?",
        "Who are the children of john?",
        "Who is the mother of alice?",
        "Are alice and bob siblings?",
        "Who are the grandparents of alice?",
        "Is mike a grandparent of bob?",
        "Tell me about John's family.",
        "Who is the father of emma?",
        "Is james a grandparent of lucy?"
    ]
    print("Family Relationship Query System")
    print("=" * 30)
    for question in questions:
        print(f"\nQuestion: {question}")
        answer = logic_lm.answer_question(question)
        print(f"Answer: {answer}")