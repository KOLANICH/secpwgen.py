import sys
import typing
import argparse
import importlib.util
import platform
import re
import string
from math import ceil, log, log2
from os import isatty
from os.path import dirname

from more_itertools import flatten

__author__ = "KOLANICH"
__license__ = "Unlicense"
__copyright__ = r"""
This is free and unencumbered software released into the public domain.

typing.Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org/>
"""

try:
	import secrets
	from secrets import choice, token_bytes
except BaseException as ex:
	raise ImportError("There is no `secrets` in this old version of python. Please download `secrets` from https://raw.githubusercontent.com/python/cpython/master/Lib/secrets.py and place it into " + dirname(string.__file__) + ". Please note that there are plenty of packages in stdlib this trick works for.") from ex

shuffle = secrets._sysrand.shuffle  # pylint:disable=protected-access


def ifModExists(modName: str) -> bool:
	return importlib.util.find_spec(modName) is not None


haveKoremutake = ifModExists("koremutake")
haveQRCode = ifModExists("qrcode")

defaultContains = ["ascii_lowercase", "ascii_uppercase", "digits", "punctuation"]

if not hasattr(string, "vowels"):
	string.vowels_lowercase = "aeiouy"
	string.vowels_uppercase = string.vowels_lowercase.upper()
	string.vowels = string.vowels_lowercase + string.vowels_uppercase


def decodeAlphabet(names: typing.List[typing.Union[str, typing.Any]]) -> typing.Set[str]:
	return set(flatten((getattr(string, g) for g in names)))


def prepareAlphabet(contains: typing.Optional[typing.List[str]] = None, remove: typing.Optional[typing.List[typing.Any]] = None) -> typing.Iterable[str]:
	if not contains:
		contains = defaultContains
	if not remove:
		remove = []
	return tuple(decodeAlphabet(contains) - decodeAlphabet(remove))


def getNBit(N):
	return token_bytes(ceil(N / 8))  # I know that that is more, but I guess more is better here and that in the original secpwgen is also used this way


def entropy(length: int, alphabetSize: int) -> float:
	return length * log2(alphabetSize)


def genRandChars(count: int, alph: typing.Iterable[str]) -> typing.Iterator[str]:
	for _ in range(count):
		yield choice(alph)


reqTransf = {
	"numerals": string.digits,
	"capitalize": string.ascii_uppercase,
	"symbols": string.punctuation
}


def enforceRequirements(passCharz, require):
	passCharz_ = set(passCharz)
	dEntr = 0
	for req in require:
		neededCharz = reqTransf[req]
		neededCharz_ = set(reqTransf[req])
		if not neededCharz_ & passCharz_:
			passCharz.extend(genRandChars(1, neededCharz))
			dEntr += entropy(1, len(neededCharz))
	return dEntr


def gen(length: int = 0, entr: None = None, contains: typing.Optional[typing.List[str]] = None, require: typing.Optional[typing.List[typing.Any]] = None, remove: typing.Optional[typing.List[typing.Any]] = None) -> typing.Tuple[float, str]:
	alph = prepareAlphabet(contains, remove)
	if entr:
		length = max(length, ceil(entr / log(len(alph))))
	entr = entropy(length, len(alph))

	passCharz = list(genRandChars(length, alph))

	if require:
		entr += enforceRequirements(passCharz, require)
		shuffle(passCharz)
	return (entr, "".join(passCharz))


remap = {
	"a": ("alphanumeric", ("ascii_lowercase", "ascii_uppercase")),
	"d": ("digits", ("digits",)),
	"h": ("hex digits", ("hexdigits",)),
	"o": ("octal digits", ("octdigits",)),
	"s": ("characters", ("punctuation",)),
	"w": ("whitespaces", ("whitespace",)),
	"p": ("all printable characters", ("printable",)),
	#"y":("3-4 letter syllables",("",))
}

removalRemap = {"no_numerals": "digits", "no_vowels": "vowels"}

optsRx = re.compile("^(-(?:[ps]e?|[ArkQ]))(.+)$")


def preprocessArgs(args: typing.List[str]) -> typing.Iterator[str]:
	args = iter(args)
	next(args)  # pylint:disable=stop-iteration-return
	for arg in args:
		m = optsRx.match(arg)
		if not m:
			yield arg
		else:
			yield from m.groups()


def genKoremutakePass(length):
	import koremutake  # pylint:disable=import-outside-toplevel

	pw = koremutake.encode(int.from_bytes(getNBit(length), sys.byteorder)).upper()
	entr = ceil(length / 8) * 8
	return (pw, entr)


def genBase64Pass(length):
	from base64 import b64encode  # pylint:disable=import-outside-toplevel

	pw = b64encode(getNBit(length)).decode(encoding="ascii")
	entr = ceil(length / 8) * 8
	return (pw, entr)


diceWarningShown = False


def getDiceDictSize():
	global diceWarningShown  # pylint:disable=global-statement
	dictSz = 8192
	if not diceWarningShown:
		sys.stderr.write("This method is not implemented. Assumming dictionary size of " + str(dictSz) + ", " + str(entropy(1, dictSz)) + " bit. The random password of the same entropy will be generated.\n")
		sys.stderr.flush()
		diceWarningShown = True
	return dictSz


def genDicePass(length):
	dictSz = getDiceDictSize()
	entr = ceil(entropy(length, dictSz))
	return gen(entr=entr)


def genRandomPass(length: int, args: argparse.Namespace) -> typing.Tuple[float, str]:
	alph = []
	if args.alphabet:
		for c in args.alphabet:
			alph.extend(remap[c][1])

	remove = [v for k, v in removalRemap.items() if getattr(args, k)]

	req = []
	for reqName in reqTransf:
		if getattr(args, reqName):
			req.append(reqName)
	return gen(length=length, contains=alph, require=req, remove=remove)


def genAndShowAPass(args: argparse.Namespace, length: int) -> None:
	pw = None
	if args.koremutake:
		if haveKoremutake:
			(pw, entr) = genKoremutakePass(length)
		else:
			raise NotImplementedError("koremutake is not installed")
	elif args.raw:
		(pw, entr) = genBase64Pass(length)
	elif args.p or args.pe or args.s or args.se:
		(pw, entr) = genDicePass(length)

	if not pw:
		(entr, pw) = genRandomPass(length, args)

	print(pw + " ;ENTROPY=" + str(entr) + " bits")

	if haveQRCode and args.qr_code:
		try:
			import qrcode  # pylint:disable=import-outside-toplevel
		except ImportError as ex:
			raise NotImplementedError("Install the qrcode package, please, in order to use this function.") from ex

		stdoutBackup = sys.stdout
		stoutIsAtty = isatty(stdoutBackup.fileno())
		if platform.system() == "Windows" and stoutIsAtty:
			try:
				import colorama  # pylint:disable=import-outside-toplevel

				colorama.init()
			except BaseException as ex:
				raise NotImplementedError("You may want to install colorama to get the better expeience") from ex
		qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_H)
		qr.add_data(pw)
		qr.print_ascii(tty=stoutIsAtty)


noEff = "No effect, it's here just for compatibility. Returns just a random string with the entropy equivalent or more than the one generated by this method in original secpwgen."


def genArgsParser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Generates a strong password.\n\nWARNING: UNLIKE THE ORIGINAL secpwgen, THE MEMORY IS NOT PROTECTED, PASSWORDS OR THE INFO NEEDED FOR THEIR GENERATION/BRUTEFORCE OPTIMIZATION MAY BE SAVED TO DISK OR LEAKED IN OTHER WAY. SIDE CHANNELS ARE NOT MITIGATED. DEPENDENCIES CAN CONTAIN BACKDOORS. YOU SHOULD BETTER USE THE C IMPLEMENTATION!",
	)
	parser.add_argument("-p", help=noEff, action="store_true")
	parser.add_argument("-pe", help=noEff, action="store_true")
	parser.add_argument("-s", help=noEff, action="store_true")
	parser.add_argument("-se", help=noEff, action="store_true")

	parser.add_argument("-A", "--alphabet", help="Specify the alphabet:\n" + "\n\t".join(("\t".join((ps, descr, repr(tp))) for (ps, (descr, tp)) in remap.items())), type=str, default="ads")

	parser.add_argument("-r", "--raw", help="base64( ceil(<length>/8) random bytes )", action="store_true")

	parser.add_argument("-k", "--koremutake", help=("koremutake( base64( ceil(<length>/8) random bytes  )" if haveKoremutake else noEff + "Install `koremutake` to make it work as intended."), action="store_true")

	# pwgen options
	parser.add_argument("-n", "--numerals", help="Require at least a single digit.", action="store_true")
	parser.add_argument("-c", "--capitalize", help="Require at least a single capital letter", action="store_true")
	parser.add_argument("--no-capitalize", help="Do not require capital letters", action="store_true")
	parser.add_argument("-y", "--symbols", help="Require at least a single symbol", action="store_true")

	parser.add_argument("-0", "--no-numerals", help="Removes numbers from alphabet. Lowers entropy.", action="store_true")
	parser.add_argument("-v", "--no-vowels", help="Disallow vowels. Usually used to disallow usual words, such as offensive ones. Lowers entropy.", action="store_true")

	#parser.add_argument("-1", help='one password per line', action='store_true')
	#parser.add_argument("-C", "--columns", help="print in columns", action='store_true')
	parser.add_argument("-N", "--num-passwords", type=int, help="Generate this count of passwords", action="store")
	#parser.add_argument("-H", "--sha1", help="use file as a seed.", action='store')

	if haveQRCode:
		parser.add_argument("-Q", "--qr-code", help="create and print a QR code", action="store_true")

	parser.add_argument("--license", help="prints unlicense", action="store_true")
	parser.add_argument("--unlicense", help="prints unlicense", action="store_true")

	parser.add_argument("lengths", type=int, default=[30], nargs="*")
	return parser


def parseArgs() -> argparse.Namespace:
	args = genArgsParser().parse_args(list(preprocessArgs(sys.argv)))
	if args.num_passwords:
		if len(args.lengths) != 1:
			raise Exception("if you use `--num-passwords` `lengths` must contain only one length")

		args.lengths *= args.num_passwords
	return args


def main() -> int:
	args = parseArgs()

	if args.license or args.unlicense:
		print(__copyright__)

	for length in args.lengths:
		genAndShowAPass(args, length)

	return 0


if __name__ == "__main__":
	sys.exit(main())
