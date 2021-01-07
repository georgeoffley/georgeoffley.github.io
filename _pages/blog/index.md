---
layout: page
title:  "Blog"
permalink: "/blog/"
---

<figure>
    <img src="https://media.giphy.com/media/116wwYf3ajIvrG/giphy.gif" />
</figure>

<ul class="posts">
    {% for post in site.posts %}
    <li><span>{{ post.date | date_to_string }}</span> » <a href="{{ post.url }}" title="{{ post.title }}">{{ post.title }}</a></li>
    {% endfor %}
</ul>