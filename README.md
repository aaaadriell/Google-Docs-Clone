## Google-Docs-Clone
This repository contains source codes for people to run a clone of the online collaborative tool, Google Docs. 

It functions in a similar manner to Google Docs:
    • Users will have to create an account, with parameters email and password
    • Users use email and password to login, accompanied with JWT auth
    • The home page will be the page where users can either view old Personal documents, view Shared With Me Documents or create a new document
    • If create a new document is selected, the program opens up a fresh, new document, allowing users to edit freely, with the autosave function built-in already
    • Users can also share selected documents with others using the recipient's email as a parameter; Recipients of shared documents can find the documents shared with them under the 'Shared With Me' portion of the home page
    • If viewing of an old document is selected, the program will open up the old document, along with the cached memory of whatever information was written and saved previously
    • Real-time collaboration feature is present as well - if 2 people are on the same document at a single time, they are able to view each other's activity


# Running Backend
1. Create venv if not created using the command 'python -m venv .venv'
2. Activate venv using the command '.venv\Scripts\activate'
3. Run the server using 'uvicorn main:app'; optionally include ' --workers <num_workers>' to run more workers in parallel instead of just utilizing one CPU core


# Running Frontend
1. npm run dev

