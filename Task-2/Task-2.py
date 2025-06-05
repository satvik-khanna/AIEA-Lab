import os
import subprocess
import tempfile
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False
    print("OpenAI API not available or credentials missing.")

def translate_to_prolog(query):
    if not OPENAI_AVAILABLE:
        print("Since OpenAI API is not available, please enter the Prolog code directly:")
        print("(Type 'END' on a new line when finished)")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        return "\n".join(lines)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates natural language queries into valid Prolog code. Return only the Prolog code without any explanations or markdown."},
                {"role": "user", "content": f"Translate this query into Prolog: {query}"}
            ],
            temperature=0.1
        )
        prolog_code = response.choices[0].message.content.strip()
        return prolog_code
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        print("Please enter the Prolog code directly:")
        print("(Type 'END' on a new line when finished)")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        return "\n".join(lines)

def run_prolog_query(prolog_code, query):
    if query.endswith('.'):
        query = query[:-1]
    
    with tempfile.NamedTemporaryFile(suffix='.pl', mode='w', delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(prolog_code)
        with tempfile.NamedTemporaryFile(suffix='.pl', mode='w', delete=False) as query_file:
            query_path = query_file.name
            query_file.write(f"""
:- initialization(main).

main :-
    consult('{tmp_path}'),
    (({query}) -> 
        writeln('RESULT_SUCCESS')
    ;
        writeln('RESULT_FAILURE')
    ),
    halt.
""")
    
    try:
        result = subprocess.run(
            ['swipl', '-q', '-l', query_path],
            capture_output=True,
            text=True,
            check=False
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        os.unlink(tmp_path)
        os.unlink(query_path)
        if stderr:
            return {"success": False, "error": stderr}
        if 'RESULT_SUCCESS' in stdout:
            return {"success": True, "output": stdout.replace('RESULT_SUCCESS', '').strip()}
        else:
            return {"success": False, "output": stdout.replace('RESULT_FAILURE', '').strip()}
    except Exception as e:
        try:
            os.unlink(tmp_path)
            os.unlink(query_path)
        except:
            pass
        return {"success": False, "error": str(e)}

def main():
    user_query = input("What would you like to express in Prolog? ")
    print("Translating to Prolog...")
    prolog_code = translate_to_prolog(user_query)
    print("\nGenerated Prolog code:")
    print(prolog_code)
    run_query_input = input("\nWould you like to run a query against this Prolog program? (y/n): ")
    if run_query_input.lower() == 'y':
        query = input("Enter your Prolog query: ")
        print("\nRunning query...")
        result = run_prolog_query(prolog_code, query)
        print("\nResults:")
        if result["success"]:
            print("Query succeeded!")
            if result["output"]:
                print(result["output"])
        else:
            print("Query failed.")
            if "error" in result and result["error"]:
                print("Error:", result["error"])
            elif "output" in result:
                print(result["output"])

if __name__ == "__main__":
    main()