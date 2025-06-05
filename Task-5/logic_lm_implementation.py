import re
from typing import Dict, Any

class ProblemFormulator:
    def __init__(self):
        self.templates = [
            {
                "pattern": r"Who is the father of (\w+)\?",
                "predicate": "father",
                "args": [lambda m: Var("X"), lambda m: m.group(1)]
            },
            {
                "pattern": r"Is (\w+) the father of (\w+)\?",
                "predicate": "father",
                "args": [lambda m: m.group(1), lambda m: m.group(2)]
            },
            {
                "pattern": r"Who is the mother of (\w+)\?",
                "predicate": "mother",
                "args": [lambda m: Var("X"), lambda m: m.group(1)]
            },
            {
                "pattern": r"Is (\w+) the mother of (\w+)\?",
                "predicate": "mother",
                "args": [lambda m: m.group(1), lambda m: m.group(2)]
            },
            {
                "pattern": r"Who (are|is) the (children|child) of (\w+)\?",
                "predicate": "child",
                "args": [lambda m: Var("X"), lambda m: m.group(3)]
            },
            {
                "pattern": r"Is (\w+) a child of (\w+)\?",
                "predicate": "child",
                "args": [lambda m: m.group(1), lambda m: m.group(2)]
            },
            {
                "pattern": r"Who (are|is) the grandparent(s)? of (\w+)\?",
                "predicate": "grandparent",
                "args": [lambda m: Var("X"), lambda m: m.group(3)]
            },
            {
                "pattern": r"Is (\w+) a grandparent of (\w+)\?",
                "predicate": "grandparent",
                "args": [lambda m: m.group(1), lambda m: m.group(2)]
            },
            {
                "pattern": r"Who (are|is) the sibling(s)? of (\w+)\?",
                "predicate": "sibling",
                "args": [lambda m: Var("X"), lambda m: m.group(3)]
            },
            {
                "pattern": r"Are (\w+) and (\w+) siblings\?",
                "predicate": "sibling",
                "args": [lambda m: m.group(1), lambda m: m.group(2)]
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
                    "query_type": "boolean" if all(isinstance(arg, str) for arg in args) else "wh-question"
                }
                return formulation
        return {
            "predicate": None,
            "args": [],
            "query_type": None
        }

class SymbolicReasoner:
    def __init__(self, knowledge_base, query_handlers):
        self.knowledge_base = knowledge_base
        self.predicate_solvers = query_handlers
    
    def reason(self, formulation: Dict[str, Any]) -> Dict[str, Any]:
        predicate = formulation.get("predicate")
        args = formulation.get("args", [])
        if not predicate or not args:
            return {"results": [], "error": "Invalid formulation"}
        solver = self.predicate_solvers.get(predicate)
        if not solver:
            return {"results": [], "error": f"No solver found for predicate '{predicate}'"}
        try:
            results = solver(*args)
            return {
                "results": results,
                "predicate": predicate,
                "args": args,
                "query_type": formulation.get("query_type")
            }
        except Exception as e:
            return {"results": [], "error": str(e)}

class ResultInterpreter:
    def interpret(self, reasoning_results: Dict[str, Any], formulation: Dict[str, Any]) -> str:
        results = reasoning_results.get("results", [])
        if not results:
            error = reasoning_results.get("error")
            if error:
                return f"Error: {error}"
            predicate = formulation.get("predicate", "")
            args = formulation.get("args", [])
            query_type = formulation.get("query_type", "")
            if query_type == "boolean":
                return f"No, {args[0]} is not the {predicate} of {args[1]} based on the available information."
            else:
                return f"I couldn't find any {predicate}s of {args[1]} based on the available information."
        predicate = reasoning_results.get("predicate", "")
        args = reasoning_results.get("args", [])
        query_type = reasoning_results.get("query_type", "")
        if query_type == "boolean":
            return f"Yes, {args[0]} is the {predicate} of {args[1]}."
        responses = []
        for result in results:
            if not result:
                responses.append("Yes, that is true.")
            else:
                var_arg_index = None
                for i, arg in enumerate(args):
                    if isinstance(arg, Var):
                        var_arg_index = i
                        break
                if var_arg_index is not None:
                    var_name = args[var_arg_index].name
                    if var_name in result:
                        value = result[var_name]
                        if predicate == "father":
                            if var_arg_index == 0:
                                responses.append(f"{value} is the father of {args[1]}.")
                            else:
                                responses.append(f"{args[0]} is the father of {value}.")
                        elif predicate == "mother":
                            if var_arg_index == 0:
                                responses.append(f"{value} is the mother of {args[1]}.")
                            else:
                                responses.append(f"{args[0]} is the mother of {value}.")
                        elif predicate == "child":
                            if var_arg_index == 0:
                                responses.append(f"{value} is a child of {args[1]}.")
                            else:
                                responses.append(f"{args[0]} is a child of {value}.")
                        elif predicate == "grandparent":
                            if var_arg_index == 0:
                                responses.append(f"{value} is a grandparent of {args[1]}.")
                            else:
                                responses.append(f"{args[0]} is a grandparent of {value}.")
                        elif predicate == "sibling":
                            if var_arg_index == 0:
                                responses.append(f"{value} is a sibling of {args[1]}.")
                            else:
                                responses.append(f"{args[0]} is a sibling of {value}.")
        if responses:
            if len(responses) == 1:
                return responses[0]
            else:
                return "\n".join(responses)
        else:
            return "No specific results found based on the available information."

class SelfRefiner:
    def refine(self, formulation: Dict[str, Any], error: str = None) -> Dict[str, Any]:
        return formulation

class Var:
    def __init__(self, name):
        self.name = name
        self.value = None
    def __repr__(self):
        return f"_{self.name}"

class LOGIC_LM:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.query_handlers = {}
        self.problem_formulator = ProblemFormulator()
        self.symbolic_reasoner = SymbolicReasoner(knowledge_base, self.query_handlers)
        self.result_interpreter = ResultInterpreter()
        self.self_refiner = SelfRefiner()
    
    def answer_question(self, question: str, max_refinements: int = 3) -> str:
        formulation = self.problem_formulator.formulate(question)
        if not formulation.get("predicate"):
            return "I don't understand that question. Could you rephrase it?"
        reasoning_results = self.symbolic_reasoner.reason(formulation)
        refinement_count = 0
        while reasoning_results.get("error") and refinement_count < max_refinements:
            formulation = self.self_refiner.refine(formulation, reasoning_results.get("error"))
            reasoning_results = self.symbolic_reasoner.reason(formulation)
            refinement_count += 1
        return self.result_interpreter.interpret(reasoning_results, formulation)