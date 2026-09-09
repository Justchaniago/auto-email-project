"""Local-only OAuth seeding tool. Never run this from the Cloud Run application."""
import argparse, json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from app.gmail.credentials import SCOPES
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('store_code'); parser.add_argument('--client-secrets',default='credentials.json'); parser.add_argument('--output',default=None); args=parser.parse_args()
    flow=InstalledAppFlow.from_client_secrets_file(args.client_secrets,SCOPES); creds=flow.run_local_server(port=0)
    output=Path(args.output or f'token_{args.store_code}.json'); output.write_text(json.dumps(json.loads(creds.to_json()),indent=2)); print(f'Wrote local token state to {output}; upload it using an explicit operator procedure.')
if __name__=='__main__': main()
