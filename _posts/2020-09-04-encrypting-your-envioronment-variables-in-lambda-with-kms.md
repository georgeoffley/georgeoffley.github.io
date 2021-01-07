---
layout: post
date: 2020-09-04 16:30
title:  "Encrypting Your Environment Variables in Lambda with KMS"
mood: happy
category: 
- AWS
tags:
- KMS
- AWS
- Lambda
---

<figure>
    <img src="/assets/images/encrypt-lambda-envs.jpg" />
</figure>

## Table Of Contents
* [Introduction](#introduction)
* [Key Management System in AWS](#key_management_system_in_aws)
* [Customer Master Keys](#customer_master_keys)
* [KMS and Lambda](#kms_and_lambda)
* [Conclusion](#conclusion)
* [Additional Notes](#additional_notes)

### Introduction <a name="introduction"></a>

Do you hate when [gnomes steal your underpants](https://youtu.be/tO5sxLapAts) for profit? I know I hate when those guys come out to steal my stuff. Unfortunately, I cannot help you prevent the theft of your undergarments, but I can help you protect some assets in AWS. Specifically, we are going to talk about encrypting environment variables in Lambda.

<!--more-->

In a previous article, I talked through about how to create a [Twitterbot using AWS Lambda](https://georgeoffley.com//aws/go/creating-a-twitter-bot-using-aws-lambda-and-go.html). I mentioned that we would talk about encrypting environment variables in my last AWS article, and this is it. Encrypting stuff is a big topic and crucial for maintaining a secure environment and not just in Lambda. 

We all know what encryption is, an ancient method for converting information into a secret code that only the correct parties would have access to. Usually, this is in the form of a key which both parties have access and can use to encrypt and decrypt. Anyone else looking at it would not be able to tell the difference between it and white noise. Records of civilization using encryption go as far back as Egyptians in 1900 B.C. using it to encode messages on the [walls of tombs](http://www.cypher.com.au/crypto_history.htm). Our modern solution for this ancient technique requires us to dive into yet another service that AWS offers, Key Management Services, or KMS.

### Key Management System in AWS <a name="key_management_system_in_aws"></a>

Key Management service, in short, is a service that allows us to manage encryption keys for various AWS services or within your AWS applications. KWS gives you a central repository to easily create, manage, and rotate your encryption keys. If you are wondering, the act of rotating encryption keys is when you generate new keys, re-encrypt all the data using the new keys, and then delete the old keys. It is an essential service in AWS.

KMS is considered a multi-tenant hardware security module or [HSM](https://en.wikipedia.org/wiki/Hardware_security_module). It’s a blade server sitting on a rack that handles the numerous clients managing keys in AWS every day. The hardware is created in a way that many clients can use the hardware but still be virtually isolated. The keys are stored in memory and not written to disk as a security measure. This way if the hardware is powered down the keys are gone and thus inaccessible. 

AWS does provide a single-tenant solution for enterprise businesses called [CloudHSM](https://aws.amazon.com/cloudhsm/). This gives more control to the client. Now, let’s have a small discussion about the captivating subject of standards in cryptography.

In 1901 the National Institute of Standards and Technology was founded as a laboratory for promoting innovation and industrial competitiveness for the science and [technology sector](https://www.nist.gov/topics/cybersecurity). Now a part of the U.S. Department of Commerce, these are the folks who set security standards for the stuff we use. In 2002 the E-Government Act was signed into law and then amended in 2014 to include new measures for [cybersecurity](https://csrc.nist.gov/projects/risk-management/detailed-overview). This included several plans to beef up encryption standards, among them is the Federal Information Process Standards or FIPS. This program sets legal requirements for U.S. government systems and the systems for any contractors. The reason I bring all this is up is that KMS in its most basic form is compliant with FIPS 140-2 Level 2 compliant. If a client were to use the single-tenant CloudHSM solution for managing keys, then they comply with FIPS 140-2 Level 3. The different levels break down into levels of security through more aggressive security solutions. You can read about all the levels [here](https://en.wikipedia.org/wiki/FIPS_140-2). A business would only need to worry about having their own CloudHSM if they are trying to comply with a specific regulation. For most of us, a regular KSM solution would work fine.

### Customer Master Keys <a name="customer_master_keys"></a>

Alright, so we know KMS is super cereal.

![Super Cereal](https://media.giphy.com/media/100J2pbO98XSrm/giphy.gif)

Now how does it work? The primary resources in KMS are the Customer Master Keys or CMKs which are logical representations of the master keys. These master keys are used to encrypt and decrypt our data. They use what is called envelope encryption for securing keys and enabling encryption.

![Key Hierarchy](https://dev-to-uploads.s3.amazonaws.com/i/9gycu8qyv3gfo20e792i.png)

When you encrypt your data whatever you encrypted is protected but you also need to protect the encryption keys. Envelope encryption is the practice of encrypting plaintext data with a data key and then encrypting the data key with another key. The data keys are strings of data used to unlock crypto functions like authentication, authorization, and encryption. The role of the master key is to keep the [data keys safe](https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#enveloping). The master keys are what is stored on the HSM and they are used to encrypt all the other keys. The CMKs you make also have metadata attached to them which track key ID, description, creation date, and key state. This metadata also includes the needed material for encryption and decrypting data. 

So, let’s see what we’re talking about. 

![KMS Dash](https://dev-to-uploads.s3.amazonaws.com/i/hcyg7crmmnwxfuzgj1nv.png)

This is the KMS dashboard where you can check out your keys. On the left, you notice that it defaults to the “Customer managed keys” menu where you can create your keys. There is also the option for AWS Managed Keys. These are keys created by AWS for various services that you use. For myself, I have a key for Lambda which is a default key I can use to encrypt environment variables. And a key for the [Cloud9 IDE AWS offers](https://aws.amazon.com/cloud9/). Cloud9 is an awesome cloud-based IDE where you won’t run into issues with Posix permissions for [stuff you make](https://twitter.com/cloudbart/status/1291450566879727619). Mini-rant over. The last option is for any “Custom key stores” you might have. Clients using AWS CloudHSM would come here to manage the keys they control within their cluster. 

So, let’s create a key

![Configure Key](https://dev-to-uploads.s3.amazonaws.com/i/x0sv0evsmvjuisdl7p4n.png)

After we hit the *Create Key* button we are taken to the *Configure Key* page. Here we can choose which [type of encryption we want](https://docs.aws.amazon.com/kms/latest/developerguide/symm-asymm-choose.html). Here we have a couple of options, **Symmetric** and **Asymmetric** encryption. 

Creating a symmetric key means we are going to create a 256-bit key that uses the same secret key to perform both the encryption and decryption processes. Something like an S4 bucket would be a great candidate for this kind of encryption which uses the [AES-256 encryption standard](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard). For me, I created a test key for encrypting environment variables using symmetric encryption.

The other option is **Asymmetric** encryption also known as public-key encryption. This will create an [RSA key pair](https://en.wikipedia.org/wiki/RSA_(cryptosystem)) used for encryption and decryption or it can also be used for signing and verification, but not both. With an asymmetric key, we create a public key used for encryption and a private key used for decryption. This we can create for something like an EC2 key pair for logging in via [SSH to an instance](https://docs.aws.amazon.com/crypto/latest/userguide/concepts-algorithms.html).

The advanced options let you use a custom store from a CloudHSM a client might own or import a key from an external key management infrastructure. When importing something from an external key management service AWS lays out some rules about how you can’t use KMS to change the key material and how you assume responsibility for some of the things AWS assumes responsibility for when you use KMS to create keys. More information is [here](https://docs.aws.amazon.com/kms/latest/developerguide/importing-keys.html#importing-keys-considerations).

![Add Label](https://dev-to-uploads.s3.amazonaws.com/i/msc48jt1kzlw1wvsg1gw.png)

Here we can add aliases for the keys. We can also add a description. We can also add [tags](https://docs.aws.amazon.com/kms/latest/developerguide/tagging-keys.html) that we might have created for tracking these assets through our billing set up. 

![Key Admin Permissions](https://dev-to-uploads.s3.amazonaws.com/i/13i5ix96zyrlqsm85fss.png)

The next screen lets us give out permissions for our key. In a large environment, you can expect to assign this key to the needed administrator. That way only that user has [permissions to administer the key using the KMS API](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html#key-policy-default-allow-administrators). Another option you also get is whether to allow admins to delete this key we are making. For any environment, I am making I would probably uncheck this. From my non-cloud sys admin perspective when you have lots of keys distributed around to many different services to have a key deleted for any reason is a recipe for potential nightmare scenarios hunting down where the key was used and redeploying the data since there’s a good chance you’re locked out of getting to it.

![Key Usage Perms](https://dev-to-uploads.s3.amazonaws.com/i/1jnascp1p7oxz1dw00fu.png)

The next screen lets us give basic permissions to use the CMK in cryptographic operations. So we can choose who can use this key to encrypt and decrypt assets. You can also add additional accounts here if we need another user that might not be on the list.

![Review](https://dev-to-uploads.s3.amazonaws.com/i/ozwzl8iagix44ni9haoc.png)

Finally, we can review and make changes to the key policy. AWS creates these rules via a JSON file. So, if you know how to navigate through the fields and understand what you are changing you are free to change the policy as you see fit. I would suggest using the GUI to do anything rather than changing the JSON directly. Unless you know what, it is you are doing. Screw around and find out at your peril.

![Peril](https://media.giphy.com/media/fWgwMmkmF8VUZ6iGPb/giphy.gif)

### KMS and Lambda <a name="kms_and_lambda"></a>

O.K. we spent a bunch of time talking about a bunch of nerd stuff. I just wanted to encrypt my environment variables. What is all this? We are almost there I promise.

![Peril](https://media.giphy.com/media/b44FwP4st6v3G/giphy.gif)

Now that we have a CMK set up let’s go into Lambda. Maybe we go into a new function that we created to test this out. Then we go into the environment variables. Now we can talk a little about how Lambda works and what impacts there are when we encrypt environment variables. Now Lambda is essentially a service that runs a single instance when called. So, no one sees your environment vars other than when a user is in the console. That said if you are sending API requests with keys and secrets anyone who might be listening on the line might be able to see it. Which is why we do all this stuff. So, before we send API secrets to Lambda lets encrypt it. 

![Env Var Menu](https://dev-to-uploads.s3.amazonaws.com/i/0ctwn8zocbq8n4uuuwws.png)

So, when we go to make our envs we have the option of encrypting them. This will encrypt them in transit and on the console too. If you notice I already created a variable and encrypted it. Under the value, there is just a random string of gibberish to the naked eye but with the key, I can decrypt the value and get the test key value. If we add a new variable, we can check the *Enable helpers for encryption in transit* under the *Encryption configuration* section which brings up the *Encrypt* button. In that section, we also get the option of using the default Lambda key that AWS creates or one of the CMKs we made earlier. I mentioned this before, but Lambda has a default key that you can use for encrypting environment variables. Makes it easy to encrypt environment variables without setting up additional CMKs. I chose to use a CMK to demonstrate KMS but using the Lambda key would probably be fine if you only have a few. When you start to scale, and you need keys for tons of stuff is where I would say using CMKs is a good idea. It gives you a lot more options for tracking and auditing. 

After hitting the *Encrypt* button we get a pop up which gives us the execution policy in the form of a JSON readout. In addition to that, we get one of my favorite things AWS gives you, the code to access your keys. I’m lazy and I will always appreciate being given the code to decode rather than digging through the API.

![Decrypt Code](https://dev-to-uploads.s3.amazonaws.com/i/1rc2ugwev2g14dcjgoh2.png)

So, I’m just going through how to decrypt and utilize your keys within your Lambda function. You can do a bit more with the API and I suggest you check out the reference [here](https://docs.aws.amazon.com/kms/latest/APIReference/Welcome.html). Similar to when you’re looking for your unencrypted env variable you can use the *os.environ()* function to grab our variable. Accept now we have just a long string of gibberish. Here is where we use the **boto3** library to do some stuff. 

Boto3 is the [AWS SDK for Python](https://github.com/boto/boto3). Here we look for the *kms* service and use the built-in [client class](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html#client) for accessing the KMS functions. Then you can see we use the [*decrypt()* function](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html#KMS.Client.decrypt) for decrypting the ciphertext we pass into it. The code also imports the **b64decode** class from the [bas64 module](https://docs.python.org/3/library/base64.html) which we use to decode the *Encrypted* var we grabbed. After that, we need to set our *EncryptionContext* which is a set of non-secret key-value pairs which represent additional authentication data. The options passed in need to match the same context that was used for encrypting the data. 

*QuickNote*
You should know that these are for symmetrical CMKs which are called symmetric because they use the same shared key for encryption and decryption. A standard asymmetric key does not support an encryption context. I used symmetric encryption for these keys so that’s what I am going through.

Finally, we can decode the ciphertext into plaintext using the *decode()* method. After all that we have access to our decrypted key using the *Decrypted* variable. As mentioned in the pictured code it’s a good idea to put all this somewhere at the beginning outside the function handler. That way we can have universal access to the decrypted key.

*QuickNote*
You might notice that we grab some additional variables using the *os.environ()* function. These are built-in in runtime environment variables which we can use to access some metadata from within the Lambda function. Check them out [here](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html#configuration-envvars-runtime).

Yay, now we can do stuff with our environment variables like pass them along to API calls. Congrats. Celebrate somehow.

![Please excuse the use of light skinned Aunt Viv](https://media.giphy.com/media/3ornkdtVzQfIRpwfug/giphy.gif)

### Conclusion <a name="conclusion"></a>

So now you know how to [protect ya neck](https://youtu.be/R0IUR4gkPIE) and encrypt ya stuff. Now encryption is a big topic. This is just one small sliver that might be relevant to using AWS Lambda. There is a long history related to cryptography. There is this great book called [The Code Book by Simon Singh](https://www.amazon.com/dp/B004IK8PLE/ref=dp-kindle-redirect?_encoding=UTF8&btkr=1) which delves deep into the history and most ancient implementations of cryptography. I highly recommend it for the power nerds among us who like reading about cryptography.

Creating policies that include encrypting your environment variables means better security and peace of mind. Lamba is a powerful engine and I am enjoying using it so far. My [Twittterbot](https://twitter.com/TheTechBruh) has been running for weeks and it’s cringy as hell so I think I’m doing something right. Now I have the tools to encrypt my API keys and secrets.

### Additional Notes <a name="additional_notes"></a>

One other service that you can also check out is the [CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html?icmpid=docs_cloudtrail_console). You can use CloudTrail and attach them to CMKs so that they can be audited. Cloud trail can keep logs of access which can be used in audits. Very useful for clients with a lot of assets to manage.

One other additional note is for those who use the [AWS CLI](https://aws.amazon.com/cli/) there are some commands which might come in handy to know. If you are also studying for an AWS Developer certification you will also need to know these.

Commands:

```
aws kms create-key - creates a unique customer-managed CMK in your AWS
aws kms encrypt - encrypts plaintext into ciphertext by using a CMK
aws kms decrypt - decrypts ciphertext that was encrypted by a KMS customer master key
aws kms re-encrypt - decrypts ciphertext and then re-encrypts it with KMS
aws kms enable-key-rotation - enables automatic rotation of the key material for the specified symmetric CMK. This cannot be done on a CML made by another account
```