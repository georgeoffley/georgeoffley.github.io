---
layout: post
date: 2020-08-17 21:00
title:  "Working with Context in Go"
mood: happy
category: 
- Go
tags:
- concurrency
- Go
---

<figure>
    <img src="/assets/images/working-with-context-in-go.jpg" />
</figure>

## Table Of Contents
* [Introduction](#introduction)
* [Context Interface](#context_interface)
* [Context in context](#context_in_context)
* [Context.Background](#context_background)
* [Context.TODO](#context_todo)
* [Context.WithCancel](#context_withcancel)
* [Context.WithDeadline](#context_withDeadline)
* [Context.WithTimeout](#context_withtimeout)
* [Context.WithValue](#context_withvalue)
* [Conclusion](#conclusion)

### Introduction <a name="introduction"></a>

When you’re having a breakdown caused by the combination of burnout and existential pain, do you get annoyed that your harried cries into the void go unanswered? Well, I can’t help with that, but I can suggest some methods for timing out calls to external or internal services. I’ve been doing research and playing with some of the standard libraries in Go and one of them I find most useful is the context library. Used to get some control over a system that might be running slowly for whatever reason or to enforce a certain level of quality for service calls this small library is a standard for a reason. For any production level systems to keep good flow control the context library is going to be necessary.
<!--This is a test-->
<!--more-->

Created by [Sameer Ajmani](https://twitter.com/Sajma) and [introduced in 2014](https://vimeo.com/115309491), the context library become a standard library with Go 1.7. If you have looked through some Go library source code you can find tons of examples [requiring a context to be passed along](https://github.com/mongodb/mongo-go-driver/blob/v1.4.0/mongo/client.go#L96). This is just one I’ve used recently. A *context* is a deadline you can pass into a running process in your code. This deadline can indicate to a process to stop running and return after a condition is met. This becomes useful when reaching out to external APIs, databases as shown above, or system commands. 

The following supposes that the reader knows about goroutines and channels and how they work together. I am going to deep dive into concurrency after writing about context as the context library is part of concurrency. For now, though, goroutines are lightweight threads that can be started for processes and channels are the pipelines used to pass data between these new processes.

### Context Interface <a name="context_interface"></a>

The context library defines a new interface called Context. The Context interface has some interesting fields laid out below:

![Context Interface](https://dev-to-uploads.s3.amazonaws.com/i/3zgq8cmkrprdfgo66niv.png)

The *Deadline* field returns the expected time the work is finished and indicates when the context should be canceled. 

The *Done* field is a channel that is closed when work done for the context should be canceled. This operation can happen asynchronously. The channel can return as nil if the associated context can never be canceled. Different context types will arrange for work to be canceled depending on the circumstances, which we will get into.

*Err* will return nil until Done is closed. After which *Err* will either return *Canceled* if the context was canceled or *DealineExceeded* if the context’s deadline has passed.

The Value field is a key-value interface which will return a value associated with the context as a key or nil if there was no value associated. Values should be used carefully as they are not for passing parameters into a function but for [request-scoped data transits processes and API boundaries](https://github.com/golang/go/blob/master/src/context/context.go#L185).

### Context in context <a name="context_in_context"></a>

When creating a context in Go it is easy to write out a static context to store and reuse. So far as I can tell from my research this is not the optimal way to work with the context library. Context should take the form needed for each use. It should be shapeless, or in the words of [Bruce Lee be like water](https://youtu.be/cJMwBwFj5nQ). Your context should flow through your code and evolve depending on the need. 

There are some exceptions to this. For higher-level processes, you can pass in an empty context when you do not yet have a context in which to pass. These can work as placeholders before being refactored. 

### Context.Background <a name="context_background"></a>

The “Background” function returns an empty non-nil context. There is no associated deadline and no cancelation to speak of. This can be typically used in the main function, for testing, or for creating a top-level context to be made into something else. Looking into the source code you can see that it doesn’t have any logic other than returning an [empty context](https://github.com/golang/go/blob/master/src/context/context.go#L208):

![Context Background](https://dev-to-uploads.s3.amazonaws.com/i/8g9hh8bxgsybws10ftld.png)

*QuickNote:*
Typically, the context is named *ctx* when it is declared. I’ve seen this in most implementations of context so if you come across *ctx* in random spots in source code there’s a good chance that it is referring to a context. 

### Context.TODO <a name="context_todo"></a>

The *TODO* function does the same thing. It returns an empty non-nil context. This again is a use case for higher-level functions that may not yet have a function available to use them. In many cases, this would be used as a placeholder when extending your program to use the context library. If you checked out the talk by Sameer Ajmani about the introduction of the context library while refactoring their code at Google they would use the *context.TODO* to start introducing context into the Google code base without breaking anything.

*QuickNote:*
One thing I will also mention is that somewhere along the way it was suggested that the *TODO* would be compatible for use in static analysis tools for seeing context propagation across a program. This from what I can tell might have been an off-hand comment from the person who wrote out the notes in the source code. I’ve been looking for the last couple of days and [from what I can tell no such tool yet exists](https://go-review.googlesource.com/c/go/+/130876/). I would investigate how to create such a tool but I’m going to go watch a movie instead.

![Context.TODO](https://dev-to-uploads.s3.amazonaws.com/i/iu484psunf8fgrlgqwe8.png)

### Context.WithCancel <a name="context_withcancel"></a>

Let’s say I’m building a website to review movies. There is a myriad of APIs designed for serving movie information. One of the recent ones I’ve come across is the [Studio Ghibli API](https://ghibliapi.herokuapp.com/#section/Studio-Ghibli-API) which is a public API we can just grab stuff from. So, for the special section of the website for Studio Ghibli movies, we’ll use this. The *WithCancel* function returns a copy of the parent context passed into it with a new *Done* channel. The new *Done* channel is closed either when the cancel function is called or when the parent context’s *Done* channel is closed. Whichever event happens first.

Below is an example in action:

![Context.WithCancel](https://dev-to-uploads.s3.amazonaws.com/i/vk990lim7irgfmgqjm4w.png)

Here we are going to simulate a process that is hanging up using the *longRunningProcess* function. In this example, the function is screwing up but we must run it before we request the JSON data from the API. The "longRunningProcess* function will return an error that will cause the *cancel()* function within the context to fire. 

For the *ghibliReq* function we will set up a simple HTTP request using the API and pass a string for locating stuff from the API. Once we set up the request, we have a case statement which will receive channel data. Depending on what happens first the select statement will be sent either the current time or the “Done” channel from the passed in context. If the *Done* channel is closed we error out, if not we will return the status code from our request.

Our main code starts with setting up the context with a new *Background()* context which is then passed into a *WithCancel()* context. The new *ctx* was passed in an empty context so nothing has happened yet. We then create a new goroutine to create a new thread and call our *longRunningProcess*. Once that is called we check for errors, which will return since we engineered it that way, and if there are errors we can call the *cancel()* function in our context. Finally, we use our context to call our request. After we run this we find that the request errored out since it took too long and the *cancel()* function was called.

In this example, we are running our *longRunningProcess* before our request because that is needed before we call our request. If the function errors out we need to be able to call “cancel()” so that we can error out the *ghibliReq()* function. The way we set it up we are calling *cancel* for our context before the function has a chance to run. This is intentional to show how the cancel works. We could easily change the *time.Sleep()* in *longRunningProcess* to say 1000 milliseconds and our request function will run before *cancel()* is called but in a production environment if the goal is to make sure we maintain the flow of the call stack we would make sure we’re not returning errors and not calling *cancel()* for this context.

*QuickNote:*
Keep in mind that a context-specific call shouldn’t be a blocking action unless necessary. It's all about keeping stuff running.

### Context.WithDeadline <a name="context_withDeadline"></a>

The *WithDeadline* function requires two arguments. One is the parent context and the other is a new time object. The function will take the parent context and adjust it to meet the new time object which was passed in. There are a couple of caveats. If you pass in a context that is already earlier than the passed in the time object then the source code will pass just return a *WithCancel* context with the same cancellation requirements as the parent which you can see [in the source](https://github.com/golang/go/blob/master/src/context/context.go#L430). The *Done* channel is closed after the new deadline expires. You can also manually return the *cancel* function or it will close when the parent context’s *Done* channel is closed. Whichever of those events happens first.

Below we can go through how the *WithDeadline* works:

![Context.WithDeadline](https://dev-to-uploads.s3.amazonaws.com/i/nwwcwgh95cejnb5kjdsh.png)

We’re going to continue with the idea that we are putting together a movie review site. To be honest it would not be far off character of me to start a website dedicated to talking exclusively about Studio Ghibli movies. The example above is doing something like the *withCancel* example. We are going to reuse a function to demonstrate our context. Reuse the stuff that works, save yourself some time. We are going to make a request and return the status of said request. The difference is how we handle our context.

Hypothetically, we need to create a whole bunch of these cascading requests and we want to make sure that everything is happening on time throughout the call stack. To keep track of time and gracefully error out when needed we can continue to use the deadlines and augment the time for the additional calls. In our example, we create a *Background* context, then pass that in along with a new time. Now we get a returned context in our *ctx* variable for about 1 second. In our example, if the request process takes longer than 1 second our context calls the cancel function and closes the *Done* channel causing the request to error out. 

We can see that this is dependent on the standards that we set. Setting a time implies that you have a decent idea about how long something should take. Which can be dependent on your server availability, internet connection, hardware constraints, etc. I have also seen people grumble about certain service level agreements guaranteeing the return of assets within a certain time frame. With the aim of usability in mind using context, deadlines can help to ensure that we can pull information at a reasonable amount of time and return if not.

### Context.WithTimeout <a name="context_withtimeout"></a>

The next relevant function is the *WithTimeout* function. This is a slight variation from the *WithDeadline* function. With a need to make something original in mind the *WithTimeout* simply returns a *WithDeadline* context with the time argument passed in added to the deadline. In other words, it acts similar to the *WithDeadline* in that it will take the parent and augment the time to return a derived context with the new time added to the time before the *cancel* function is called and the *Done* channel is closed. I’ll make this example even simpler:

![Context.WithTimeout](https://dev-to-uploads.s3.amazonaws.com/i/dcw4vhshlsephh1c19na.png)

Same as the example before we set the timeout to close the “Done” channel after the allotted time. In our case, if after a half-second, we’re still waiting for the call we timeout. I love the HTTP go library because it has a built-in function for returning a shadow copy of the request with the [new context added](https://golang.org/src/net/http/request.go?s=12980:13039#L341).

### Context.WithValue <a name="context_withvalue"></a>

The last bit of the source I am going to touch on is the *ContextWithValue* function. This one is a bit controversial since the nature of it, from what I can tell, goes against what the context should be. A context should be a way to ensure that we keep data flowing to and from our programs. The value part of the context though can be used to carry information back and forth. The function allows you to pass in a key-value interface to pass around with your calls.

From the original post about context [“WithValue provides a way to associate request-scoped values with a context”](https://blog.golang.org/context). I’m going to talk a little about what it shouldn’t be used for. Most articles or tutorials I came across seem to agree that passing information that lives outside of the request itself was a bad idea. DB connections, function arguments, anything that is not created and destroyed within that request is probably not a great design pattern. That said passing values along your context can be useful. 

Let’s check out some code:

![Context.WithValue](https://dev-to-uploads.s3.amazonaws.com/i/nrbebpw31tc4nmwjj285.png)

We’re going to use the same code from the last example. Only in this case, we are going to create a new function which will calculate a fake request ID. Say I want to keep a database of all my requests, because… I don’t know, I’m a psychopath. Or I work for the NSA and I’m making some spyware to look in on my ex in the name of national security. And because they don’t train me in operational intelligence, I don’t know how to discern the data that indicates something and white noise, so I collect everything. Even innocuous calls to an open API for looking up animated movie information. I’m very tired right now.

In our example we do the same as above; set up a context with a timeout for half a second. Only now we have a helper method that will calculate a new request ID and we will use the context to pass that ID along within the context as a new interface that we can access and do stuff with. In this fake scenario, we would log this and close out the context. This will conform to our self-imposed standard of keeping only information relevant to that call. Yay information!

There is a lot more to be explored about passing along values within a context. I have seen articles where middleware is used to do stuff in between two services to make something work better. I might dig deeper into this and since it’s a bit outside the scope of this I might write about it later. Who knows, I need sleep.

### Conclusion <a name="conclusion"></a>

The context library helps to add some sanity to calls in our program. When designing a program incorporating a context in our functions should happen as early as possible. As mentioned, before it is easy to create our function with a *TODO* as a placeholder and go back when refactoring. It was also mentioned that programs should be created to fail gracefully as well. Take it from someone who spent a long time creating vague fail messages which no one can understand including me. A user should not have to know that a call to something failed just that they aren’t getting their movie title in half a second. 

A cool way to picture how useful these contexts can be was touched on in Sameer’s talk. He spoke about the practice of hedged calls where you call out redundant services and take the one which takes less time. It’s all about speed and optimization with them Google people. That is one way in which creating a context to flow through your program would be helpful. When one comes back you cancel out the other which releases the resources that thread might have been using up. The context is a small but very powerful library, it should be used often and with plenty of thought and planning into how it should flow into your program. My hope after reading this is that we all come away with a better understanding of context and how we can use it! If you liked this, had questions and or comments, or you just want to berate me on how much the Last Jedi sucked (it was an imperfect but powerful movie for a world not yet ready for it) hit me up on [Twitter](https://twitter.com/georgeoffley)! I love topical references.
