#!/usr/bin/env python
#
# $Id$
#
# PyXMLSec example: Signing a file with a dynamicaly created template.
#
# Signs a file using a dynamicaly created template and key from PEM file.
# The signature has one reference with one enveloped transform to sign
# the whole document except the <dsig:Signature/> node itself.
#
# Usage: 
#	./sign2.py <xml-doc> <pem-key> 
#
# Example:
#	./sign2.py sign2-doc.xml rsakey.pem > sign2-res.xml
#
# The result signature could be validated using verify1 example:
#	./verify1.py sign2-res.xml rsapub.pem
#
# This is free software; see COPYING file in the source
# distribution for preciese wording.
# 
# Copyright (C) 2003-2004 Valery Febvre <vfebvre@easter-eggs.com>
#

import sys
sys.path.insert(0, '../')

import libxml2
import xmlsec

def main():
    assert(sys.argv)
    if len(sys.argv) < 3:
        print "Error: wrong number of arguments."
        print "Usage: %s <xml-tmpl> <pem-key>" % sys.argv[0]
        return sys.exit(1)
    
    # Init libxml library
    libxml2.initParser()
    libxml2.substituteEntitiesDefault(1)

    # Init xmlsec library
    if xmlsec.init() < 0:
        print "Error: xmlsec initialization failed."
        return sys.exit(-1)
    
    # Check loaded library version
    if xmlsec.checkVersion() != 1:
	print "Error: loaded xmlsec library version is not compatible.\n"
	sys.exit(-1)

    # Init crypto library
    if xmlsec.cryptoAppInit(None) < 0:
        print "Error: crypto initialization failed."
    
    # Init xmlsec-crypto library
    if xmlsec.cryptoInit() < 0:
        print "Error: xmlsec-crypto initialization failed."

    res = sign_file(sys.argv[1], sys.argv[2])

    # Shutdown xmlsec-crypto library
    xmlsec.cryptoShutdown()

    # Shutdown crypto library
    xmlsec.cryptoAppShutdown()

    # Shutdown xmlsec library
    xmlsec.shutdown()

    # Shutdown LibXML2
    libxml2.cleanupParser()

    sys.exit(res)

# Signs the xml_file using private key from key_file and dynamicaly
# created enveloped signature template.
# Returns 0 on success or a negative value if an error occurs.
def sign_file(xml_file, key_file):
    assert(xml_file)
    assert(key_file)

    # Load template
    doc = libxml2.parseFile(xml_file)
    if doc is None or doc.getRootElement() is None:
	print "Error: unable to parse file \"%s\"" % xml_file
        return cleanup(doc)

    # Create signature template for RSA-SHA1 enveloped signature
    signNode = xmlsec.TmplSignature(doc, xmlsec.transformExclC14NId(),
                                    xmlsec.transformRsaSha1Id(), None)
    if signNode is None:
        print "Error: failed to create signature template"
        return cleanup(doc)
    
    # Add <dsig:Signature/> node to the doc
    doc.getRootElement().addChild(signNode)

    # Add reference
    refNode = signNode.addReference(xmlsec.transformSha1Id(),
                                    None, None, None)
    if refNode is None:
        print "Error: failed to add reference to signature template"
        return cleanup(doc)

    # Add enveloped transform
    if refNode.addTransform(xmlsec.transformEnvelopedId()) is None:
        print "Error: failed to add enveloped transform to reference"
        return cleanup(doc)

    # Add <dsig:KeyInfo/> and <dsig:KeyName/> nodes to put key name
    # in the signed document
    keyInfoNode = signNode.ensureKeyInfo(None)
    if keyInfoNode is None:
        print "Error: failed to add key info"
        return cleanup(doc)
    
    keyNameInfo = keyInfoNode.addKeyName(None)
    if keyNameInfo is None:
        print "Error: failed to add key name"
        return cleanup(doc)

    # Create signature context, we don't need keys manager in this example
    dsig_ctx = xmlsec.DSigCtx()
    if dsig_ctx is None:
        print "Error: failed to create signature context"
        return cleanup(doc)

    # Load private key, assuming that there is not password
    key = xmlsec.cryptoAppKeyLoad(key_file, xmlsec.KeyDataFormatPem,
                                  None, None, None)
    if key is None:
        print "Error: failed to load private pem key from \"%s\"" % key_file
        return cleanup(doc, dsig_ctx)
    dsig_ctx.signKey = key

    # Set key name to the file name, this is just an example!
    if key.setName(key_file) < 0:
        print "Error: failed to set key name for key from \"%s\"" % key_file
        return cleanup(doc, dsig_ctx)

    # Sign the template
    if dsig_ctx.sign(signNode) < 0:
        print "Error: signature failed"
        return cleanup(doc, dsig_ctx)

    # Print signed document to stdout
    doc.dump("-")

    # Success
    return cleanup(doc, dsig_ctx, 1)


def cleanup(doc=None, dsig_ctx=None, res=-1):
    if dsig_ctx is not None:
        dsig_ctx.destroy()
    if doc is not None:
        doc.freeDoc()
    return res


if __name__ == "__main__":
    main()
