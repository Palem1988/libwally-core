import unittest
from util import *

SCRIPT_TYPE_P2PKH = 0x2
SCRIPT_TYPE_P2SH = 0x4
SCRIPT_TYPE_MULTISIG = 0x20

SCRIPT_HASH160 = 0x1
SCRIPT_SHA256  = 0x2

SCRIPTPUBKEY_P2PKH_LEN = 25
SCRIPTPUBKEY_P2SH_LEN = 23
HASH160_LEN = 20
SCRIPTSIG_P2PKH_MAX_LEN = 140

PK, PK_LEN = make_cbuffer('11' * 33) # Fake compressed pubkey
PKU, PKU_LEN = make_cbuffer('11' * 65) # Fake uncompressed pubkey
SH, SH_LEN = make_cbuffer('11' * 20)  # Fake script hash
MPK_2, MPK_2_LEN = make_cbuffer('11' * 33 * 2) # Fake multiple (2) pubkeys
MPK_3, MPK_3_LEN = make_cbuffer('11' * 33 * 3) # Fake multiple (3) pubkeys
MPK_17, MPK_17_LEN = make_cbuffer('11' * 33 * 17) # Fake multiple (17) pubkeys

SIG, SIG_LEN = make_cbuffer('11' * 64) # Fake signature
SIG_LARGE, SIG_LARGE_LEN = make_cbuffer('ff' * 64) # Fake out of range signature
SIG_COUPLE, SIG_COUPLE_LEN = make_cbuffer('11' * 64 * 2) # Fake couple of signatures
SIG_DER, SIG_DER_LEN = make_cbuffer('30450220' + '11'*32 + '0220' + '11'*32 + '01') # Fake DER encoded sig

RS_1of2, RS_1of2_LEN = make_cbuffer('5121' + '11'*33 + '21' + '11'*33 + '52ae') # Fake 1of2 redeem script
RS_2of2, RS_2of2_LEN = make_cbuffer('5221' + '11'*33 + '21' + '11'*33 + '52ae') # Fake 2of2 redeem script

class ScriptTests(unittest.TestCase):

    def test_scripttpubkey_get_type(self):
        """Tests for script analysis"""
        # Test invalid args, we test results with the functions that make scripts
        in_, in_len = make_cbuffer('00' * 16)
        for b, b_len in [(None, in_len), (in_, 0)]:
            ret, written = wally_scriptpubkey_get_type(b, b_len)
            self.assertEqual(ret, WALLY_EINVAL)
            self.assertEqual(written, 0)

    def test_scriptpubkey_p2pkh_from_bytes(self):
        """Tests for creating p2pkh scriptPubKeys"""
        # Invalid args
        out, out_len = make_cbuffer('00' * SCRIPTPUBKEY_P2PKH_LEN)
        invalid_args = [
            (None, PK_LEN, SCRIPT_HASH160, out, out_len), # Null bytes
            (PK, 0, SCRIPT_HASH160, out, out_len), # Empty bytes
            (PK, PK_LEN, SCRIPT_SHA256, out, out_len), # Unsupported flags
            (PK, PK_LEN, SCRIPT_HASH160, None, out_len), # Null output
            (PK, PK_LEN, SCRIPT_HASH160, out, SCRIPTPUBKEY_P2PKH_LEN-1), # Short output len
            (PK, PK_LEN, 0, out, out_len), # Pubkey w/o SCRIPT_HASH160
            (PKU, PKU_LEN, 0, out, out_len), # Uncompressed pubkey w/o SCRIPT_HASH160
        ]
        for args in invalid_args:
            ret = wally_scriptpubkey_p2pkh_from_bytes(*args)
            self.assertEqual(ret, (WALLY_EINVAL, 0))

        # Valid cases
        valid_args = [
            (PK, PK_LEN, SCRIPT_HASH160, out, out_len),
            (PKU, PKU_LEN, SCRIPT_HASH160, out, out_len),
            (PKU, HASH160_LEN, 0, out, out_len),
        ]
        for args in valid_args:
            ret = wally_scriptpubkey_p2pkh_from_bytes(*args)
            self.assertEqual(ret, (WALLY_OK, SCRIPTPUBKEY_P2PKH_LEN))
            ret = wally_scriptpubkey_get_type(out, SCRIPTPUBKEY_P2PKH_LEN)
            self.assertEqual(ret, (WALLY_OK, SCRIPT_TYPE_P2PKH))

    def test_scriptpubkey_p2sh_from_bytes(self):
        """Tests for creating p2sh scriptPubKeys"""
        # Invalid args
        out, out_len = make_cbuffer('00' * SCRIPTPUBKEY_P2SH_LEN)
        invalid_args = [
            (None, SH_LEN, SCRIPT_HASH160, out, out_len), # Null bytes
            (SH, 0, SCRIPT_HASH160, out, out_len), # Empty bytes
            (SH, SH_LEN, SCRIPT_SHA256, out, out_len), # Unsupported flags
            (SH, SH_LEN, SCRIPT_HASH160, None, out_len), # Null output
            (SH, SH_LEN, SCRIPT_HASH160, out, SCRIPTPUBKEY_P2SH_LEN-1), # Short output len
        ]
        for args in invalid_args:
            ret = wally_scriptpubkey_p2sh_from_bytes(*args)
            self.assertEqual(ret, (WALLY_EINVAL, 0))

        # Valid cases
        valid_args = [
            (SH, SH_LEN, SCRIPT_HASH160, out, out_len),
            (SH, SH_LEN, 0, out, out_len),
        ]
        for args in valid_args:
            ret = wally_scriptpubkey_p2sh_from_bytes(*args)
            self.assertEqual(ret, (WALLY_OK, SCRIPTPUBKEY_P2SH_LEN))
            ret = wally_scriptpubkey_get_type(out, SCRIPTPUBKEY_P2SH_LEN)
            self.assertEqual(ret, (WALLY_OK, SCRIPT_TYPE_P2SH))

    def test_scriptpubkey_multisig_from_bytes(self):
        """Tests for creating multisig scriptPubKeys"""
        # Invalid args
        out, out_len = make_cbuffer('00' * 33 * 3)
        invalid_args = [
            (None, MPK_2_LEN, 1, 0, out, out_len), # Null bytes
            (MPK_2, 0, 1, 0, out, out_len), # Empty bytes
            (MPK_2, MPK_2_LEN+1, 1, 0, out, out_len), # Unsupported bytes len
            (SH, SH_LEN, 1, 0, out, out_len), # Too few pubkeys
            (MPK_17, MPK_17_LEN, 1, 0, out, out_len), # Too many pubkeys
            (MPK_2, MPK_2_LEN, 0, 0, out, out_len), # Too low threshold
            (MPK_2, MPK_2_LEN, 17, 0, out, out_len), # Too high threshold
            (MPK_2, MPK_2_LEN, 3, 0, out, out_len), # Inconsistent threshold
            (MPK_2, MPK_2_LEN, 1, SCRIPT_HASH160, out, out_len), # Unsupported flags
            (MPK_2, MPK_2_LEN, 1, 0, None, out_len), # Null output
        ]
        for args in invalid_args:
            ret = wally_scriptpubkey_multisig_from_bytes(*args)
            self.assertEqual(ret, (WALLY_EINVAL, 0))

        # Valid cases
        out, out_len = make_cbuffer('00' * 33 * 4)
        valid_args = [
            (MPK_2, MPK_2_LEN, 1, 0, out, out_len), # 1of2
            (MPK_2, MPK_2_LEN, 2, 0, out, out_len), # 2of2
            (MPK_3, MPK_3_LEN, 1, 0, out, out_len), # 1of3
            (MPK_3, MPK_3_LEN, 2, 0, out, out_len), # 2of3
            (MPK_3, MPK_3_LEN, 3, 0, out, out_len), # 3of3
        ]
        for args in valid_args:
            script_len = 3 + (args[1] // 33 * (33 + 1))
            ret = wally_scriptpubkey_multisig_from_bytes(*args)
            self.assertEqual(ret, (WALLY_OK, script_len))
            ret = wally_scriptpubkey_get_type(out, script_len)
            self.assertEqual(ret, (WALLY_OK, SCRIPT_TYPE_MULTISIG))

    def test_scriptpubkey_csv_2of2_then_1_from_bytes(self):
        """Tests for creating csv 2of2 then 1 scriptPubKeys"""
        # Invalid args
        out, out_len = make_cbuffer('00' * 33 * 3)
        invalid_args = [
            (None, MPK_2_LEN, 1, 0, out, out_len), # Null bytes
            (MPK_2, 0, 1, 0, out, out_len), # Empty bytes
            (MPK_2, MPK_2_LEN+1, 1, 0, out, out_len), # Unsupported bytes len
            (MPK_2, MPK_2_LEN, 0, 0, out, out_len), # 0 csv blocks
            (MPK_2, MPK_2_LEN, 0x10000, 0, out, out_len), # Too many csv blocks
            (MPK_2, MPK_2_LEN, 1, SCRIPT_HASH160, out, out_len), # Unsupported flags
            (MPK_2, MPK_2_LEN, 1, 0, None, out_len), # Null output
        ]
        for args in invalid_args:
            ret = wally_scriptpubkey_csv_2of2_then_1_from_bytes(*args)
            self.assertEqual(ret, (WALLY_EINVAL, 0))

        # Valid cases
        valid_args = [
            (MPK_2, MPK_2_LEN, 1, 0, out, out_len),
            (MPK_2, MPK_2_LEN, 0x8000, 0, out, out_len),
        ]
        for args in valid_args:
            csv_len = 1 + (args[2] > 0x7f) + (args[2] > 0x7fff)
            script_len = 2 * (33 + 1) + 9 + 1 + csv_len
            ret = wally_scriptpubkey_csv_2of2_then_1_from_bytes(*args)
            self.assertEqual(ret, (WALLY_OK, script_len))

    def test_scriptpubkey_csv_2of3_then_2_from_bytes(self):
        """Tests for creating csv 2of3 then 2 scriptPubKeys"""
        # Invalid args
        out, out_len = make_cbuffer('00' * 33 * 4)
        invalid_args = [
            (None, MPK_3_LEN, 1, 0, out, out_len), # Null bytes
            (MPK_3, 0, 1, 0, out, out_len), # Empty bytes
            (MPK_3, MPK_3_LEN+1, 1, 0, out, out_len), # Unsupported bytes len
            (MPK_3, MPK_3_LEN, 0, 0, out, out_len), # 0 csv blocks
            (MPK_3, MPK_3_LEN, 0x10000, 0, out, out_len), # Too many csv blocks
            (MPK_3, MPK_3_LEN, 1, SCRIPT_HASH160, out, out_len), # Unsupported flags
            (MPK_3, MPK_3_LEN, 1, 0, None, out_len), # Null output
        ]
        for args in invalid_args:
            ret = wally_scriptpubkey_csv_2of3_then_2_from_bytes(*args)
            self.assertEqual(ret, (WALLY_EINVAL, 0))

        # Valid cases
        valid_args = [
            (MPK_3, MPK_3_LEN, 1, 0, out, out_len),
            (MPK_3, MPK_3_LEN, 0x8000, 0, out, out_len),
        ]
        for args in valid_args:
            csv_len = 1 + (args[2] > 0x7f) + (args[2] > 0x7fff)
            script_len = 3 * (33 + 1) + 13 + 1 + csv_len
            ret = wally_scriptpubkey_csv_2of3_then_2_from_bytes(*args)
            self.assertEqual(ret, (WALLY_OK, script_len))

    def test_scriptsig_p2pkh(self):
        """Tests for creating p2pkh scriptsig"""
        # From DER
        # Invalid args
        out, out_len = make_cbuffer('00' * SCRIPTSIG_P2PKH_MAX_LEN)
        invalid_args = [
            (None, PK_LEN, SIG_DER, SIG_DER_LEN, out, out_len), # Null pubkey
            (PK, 32, SIG_DER, SIG_DER_LEN, out, out_len), # Unsupported pubkey length
            (PK, PK_LEN, None, SIG_DER_LEN, out, out_len), # Null sig
            (PK, PK_LEN, SIG_DER, 0, out, out_len), # Too short len sig
            (PK, PK_LEN, SIG_DER, 74, out, out_len), # Too long len sig
            (PK, PK_LEN, SIG_DER, SIG_DER_LEN, None, out_len), # Null output
        ]
        for args in invalid_args:
            ret = wally_scriptsig_p2pkh_from_der(*args)
            self.assertEqual(ret, (WALLY_EINVAL, 0))

        # Valid cases
        valid_args = [
            (PK, PK_LEN, SIG_DER, SIG_DER_LEN, out, out_len),
            (PKU, PKU_LEN, SIG_DER, SIG_DER_LEN, out, out_len),
        ]
        for args in valid_args:
            ret = wally_scriptsig_p2pkh_from_der(*args)
            self.assertEqual(ret, (WALLY_OK, args[1] + args[3] + 2))

        # From sig
        # Invalid args
        out, out_len = make_cbuffer('00' * 140)
        invalid_args = [
            (PK, PK_LEN, SIG, SIG_LEN, 0x100, out, out_len),
            (PK, PK_LEN, SIG_LARGE, SIG_LARGE_LEN, 0xff, out, out_len), # is it correct to test it here?
        ]
        for args in invalid_args:
            ret = wally_scriptsig_p2pkh_from_sig(*args)
            self.assertEqual(ret, (WALLY_EINVAL, 0))

        # Valid cases
        valid_args = [
            (PK, PK_LEN, SIG, SIG_LEN, 0x01, out, out_len),
            (PKU, PKU_LEN, SIG, SIG_LEN, 0x01, out, out_len),
        ]
        for args in valid_args:
            ret = wally_scriptsig_p2pkh_from_sig(*args)
            self.assertEqual(ret, (WALLY_OK, args[1] + args[3] + 9))

    def test_scriptsig_multisig(self):
        """Tests for creating multisig scriptsig"""

        def c_sighash(s):
            c_sighash = (c_uint * len(s))()
            for i, n in enumerate(s):
                c_sighash[i] = n
            return c_sighash

        # Invalid args
        out, out_len = make_cbuffer('')
        invalid_args = [
            (None, RS_1of2_LEN, SIG, SIG_LEN, c_sighash([0x01]), 1, 0, out, out_len), # Null script
            (RS_1of2, 0, SIG, SIG_LEN, c_sighash([0x01]), 1, 0, out, out_len), # Empty script
            (RS_1of2, RS_1of2_LEN, None, SIG_LEN, c_sighash([0x01]), 1, 0, out, out_len), # Null bytes
            (RS_1of2, RS_1of2_LEN, SIG, 0, c_sighash([0x01]), 1, 0, out, out_len), # Empty bytes or too few sigs
            (RS_1of2, RS_1of2_LEN, SIG, SIG_LEN+1, c_sighash([0x01]), 1, 0, out, out_len), # Unsupported bytes len
            (RS_1of2, RS_1of2_LEN, SIG, 17, c_sighash([0x01]), 1, 0, out, out_len), # Too many sigs
            (RS_1of2, RS_1of2_LEN, SIG, SIG_LEN, None, 1, 0, out, out_len), # Null sighash
            (RS_1of2, RS_1of2_LEN, SIG, SIG_LEN, c_sighash([0x01]), 2, 0, out, out_len), # Inconsistent sighash length
            (RS_1of2, RS_1of2_LEN, SIG, SIG_LEN, c_sighash([0x01]), 1, 1, out, out_len), # Unsupported flags
            (RS_1of2, RS_1of2_LEN, SIG, SIG_LEN, c_sighash([0x01]), 1, 0, None, out_len), # Null output
        ]
        for args in invalid_args:
            ret = wally_scriptsig_multisig_from_bytes(*args)
            self.assertEqual(ret, (WALLY_EINVAL, 0))

        # Valid cases
        valid_args = [
            (RS_1of2, RS_1of2_LEN, SIG, SIG_LEN, c_sighash([0x01]), 1, 0, out, out_len),
            (RS_1of2, RS_1of2_LEN, SIG, SIG_LEN, c_sighash([0x80]), 1, 0, out, out_len),
            (RS_2of2, RS_2of2_LEN, SIG, SIG_LEN, c_sighash([0x01]), 1, 0, out, out_len),
            (RS_2of2, RS_2of2_LEN, SIG_COUPLE, SIG_COUPLE_LEN, c_sighash([0x01, 0x02]), 2, 0, out, out_len),
        ]
        for args in valid_args:
            ret = wally_scriptsig_multisig_from_bytes(*args)
            self.assertEqual(ret, (WALLY_OK, 73 + 72 * args[5]))

    def test_script_push_from_bytes(self):
        """Tests for encoding script pushes"""
        out, out_len = make_cbuffer('00' * 165536)
        for data, prefix in {'00' * 75: '4b',
                             '00' * 76: '4c4c',
                             '00' * 255: '4cff',
                             '00' * 256: '4d0001'}.items():

            in_, in_len = make_cbuffer(data)
            ret, written = wally_script_push_from_bytes(in_, in_len, 0, out, out_len)
            self.assertEqual(ret, WALLY_OK)
            self.assertEqual(written, len(data)/2 + len(prefix)/2)
            self.assertEqual(h(out[:written]), utf8(prefix + data))

            # Too short out_len returns the required number of bytes
            ret, written = wally_script_push_from_bytes(in_, in_len, 0, out, 20)
            self.assertEqual(ret, WALLY_OK)
            self.assertEqual(written, len(data)/2 + len(prefix)/2)

    def test_wally_witness_program_from_bytes(self):
        valid_cases = [('00' * 20, 0),
                       ('00' * 32, 0),
                       ('00' * 50, SCRIPT_HASH160),
                       ('00' * 50, SCRIPT_SHA256)]

        out, out_len = make_cbuffer('00' * 100)
        for data, flags in valid_cases:
            in_, in_len = make_cbuffer(data)
            ret, written = wally_witness_program_from_bytes(in_, in_len, flags, out, out_len)
            self.assertEqual(ret, WALLY_OK)

        invalid_cases = [('00' * 50, 0), # Invalid unhashed length
                ]
        for data, flags in invalid_cases:
            in_, in_len = make_cbuffer(data)
            ret, written = wally_witness_program_from_bytes(in_, in_len, flags, out, out_len)
            self.assertEqual(ret, WALLY_EINVAL)


if __name__ == '__main__':
    unittest.main()
