import json, tempfile, unittest
from pathlib import Path
from patala_research_ci.merkle import merkle_root, inclusion_proof, verify_inclusion
from patala_research_ci.attestation import generate_ed25519_keypair, statement_for, sign_statement, verify_envelope

class MerkleAttestationTests(unittest.TestCase):
    def test_inclusion_and_tamper(self):
        leaves=[b'a',b'b',b'c',b'd']; root=merkle_root(leaves); proof=inclusion_proof(leaves,2)
        self.assertTrue(verify_inclusion(b'c',proof,root)); self.assertFalse(verify_inclusion(b'X',proof,root))
    def test_ed25519_attestation(self):
        try: import cryptography  # noqa
        except ImportError: self.skipTest('cryptography not installed')
        with tempfile.TemporaryDirectory() as td:
            priv=Path(td)/'k'; pub=Path(td)/'k.pub'; generate_ed25519_keypair(priv,pub)
            st=statement_for('claim:1','sha256:'+'0'*64,'https://patala.dev/attestation/verification/v1',{'status':'PASS'})
            env=sign_statement(st,priv)
            ok,payload=verify_envelope(env,pub); self.assertTrue(ok); self.assertEqual(payload['predicate']['status'],'PASS')
            d=env.to_dict(); sig=d['signatures'][0]['sig']; d['signatures'][0]['sig']=('A' if sig[0]!='A' else 'B')+sig[1:]
            ok,_=verify_envelope(d,pub); self.assertFalse(ok)

if __name__=='__main__': unittest.main()
