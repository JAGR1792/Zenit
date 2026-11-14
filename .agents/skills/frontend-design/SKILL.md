---
name: frontend-design
description: Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults.
license: Complete terms in LICENSE.txt
---
# Frontend Design

Approach
 this as the design lead at a small studio kn
own for giving every client a visual identity
 that could not be mistaken for anyone else's
. This client has already rejected proposals 
that felt templated, and is paying for a dist
inctive point of view: make deliberate, opini
onated choices about palette, typography, and
 layout that are specific to this brief, and 
take one real aesthetic risk you can justify.


## Ground it in the subject

If the brief d
oes not pin down what the product or subject 
is, pin it yourself before designing: name on
e concrete subject, its audience, and the pag
e's single job, and state your choice. If the
re's any information in your memory about the
 human's preferences, context about what they
're building, or designs you've made before �
�� use that as a hint. The subject's own worl
d, its materials, instruments, artifacts, and
 vernacular, is where distinctive choices com
e from. Build with the brief's real content a
nd subject matter throughout.

## Design prin
ciples

For web designs, the hero is a thesis
. Open with the most characteristic thing in 
the subject's world, in whatever form makes s
ense for it: a headline, an image, an animati
on, a live demo, an interactive moment. Be de
liberate with your choice: a big number with 
a small label, supporting stats, and a gradie
nt accent is the template answer, only use if
 that's truly the best option.

Typography ca
rries the personality of the page. Pair the d
isplay and body faces deliberately, not the s
ame families you would reach for on any other
 project, and set a clear type scale with int
entional weights, widths, and spacing. Make t
he type treatment itself a memorable part of 
the design, not a neutral delivery vehicle fo
r the content.

Structure is information. Str
uctural devices, numbering, eyebrows, divider
s, labels, should encode something true about
 the content, not decorate it. Many generic d
esigns use numbered markers (01 / 02 / 03), b
ut that's only appropriate if the content act
ually is a sequence - like a real process or 
a typed timeline where order carries informat
ion the reader needs. Question if choices lik
e numbered markers actually make sense before
 incorporating them.

Leverage motion deliber
ately. Think about where and if animation can
 serve the subject: a page-load sequence, a s
croll-triggered reveal, hover micro-interacti
ons, ambient atmosphere. An orchestrated mome
nt usually lands harder than scattered effect
s; choose what the direction calls for. Howev
er, sometimes less is more, and extra animati
on contributes to the feeling that the design
 is AI-generated.

Match complexity to the vi
sion. Maximalist directions need elaborate ex
ecution; minimal directions need precision in
 spacing, type, and detail. Elegance is execu
ting the chosen vision well.

Consider writte
n content carefully. Often a design brief may
 not contain real content, and it's up to you
 to come up with copy. Copy can make a design
 feel as templated as the design itself. See 
the below section on writing for more guidanc
e.

## Process: brainstorm, explore, plan, cr
itique, build, critique again

For calibratio
n: AI-generated design right now clusters aro
und three looks: (1) a warm cream background 
(near #F4F1EA) with a high-contrast serif dis
play and a terracotta accent; (2) a near-blac
k background with a single bright acid-green 
or vermilion accent; (3) a broadsheet-style l
ayout with hairline rules, zero border-radius
, and dense newspaper-like columns. All three
 are legitimate for some briefs, but they are
 defaults rather than choices, and they appea
r regardless of subject. Where the brief pins
 down a visual direction, follow it exactly �
�� the brief's own words always win, includin
g when it asks for one of these looks. Where 
it leaves an axis free, don't spend that free
dom on one of these defaults. Just like a hum
an designer who's hired, there's often a care
ful balance between doing what you're good at
 and taking each project as a chance to exper
iment and learn.

Work in two passes. First, 
brainstorm a short design plan based on the h
uman's design brief: create a compact token s
ystem with color, type, layout, and signature
. Color: describe the palette as 4–6 named 
hex values. Type: the typefaces for 2+ roles 
(a characterful display face that's used with
 restraint, a complementary body face, and a 
utility face for captions or data if needed).
 Layout: a layout concept, using one-sentence
 prose descriptions and ASCII wireframes to i
deate and compare. Signature: the single uniq
ue element this page will be remembered by th
at embodies the brief in an appropriate way.


Then review that plan against the brief befo
re building: if any part of it reads like the
 generic default you would produce for any si
milar page (work through a similar prompt to 
see if you arrive somewhere similar) rather t
han a choice made for this specific brief —
 revise that part, say what you changed and w
hy. Only after you've confirmed the relative 
uniqueness of your design plan should you sta
rt to write the code, following the revised p
lan exactly and deriving every color and type
 decision from it.

When writing the code, be
 careful of structuring your CSS selector spe
cificities. It's easy to generate CSS classes
 that cancel each other out (especially with 
a type-based selector like .section and a ele
ment-based selector like .cta). This can happ
en often with paddings/margins between sectio
ns.

Try to do a lot of this planning and ite
ration in your thinking, and only show ideas 
to the user when you have higher confidence i
t'll delight them.

## Restraint and self-cri
tique

Spend your boldness in one place. Let 
the signature element be the one memorable th
ing, keep everything around it quiet and disc
iplined, and cut any decoration that does not
 serve the brief. Not taking a risk can be a 
risk itself! Build to a quality floor without
 announcing it: responsive down to mobile, vi
sible keyboard focus, reduced motion respecte
d. Critique your own work as you build, takin
g screenshots if your environment supports it
 – a picture is worth 1000 tokens. Consider
 Chanel's advice: before leaving the house, t
ake a look in the mirror and remove one acces
sory. Human creators have memory and always t
ry to do something new, so if you have a spac
e to quickly jot down notes about what you've
 tried, it can help you in future passes.

##
 More on writing in design

Words appear in a
 design for one reason: to make it easier to 
understand, and therefore easier to use. They
 are design material, not decoration. Bring t
he same intentionality to copy that you would
 bring to spacing and color. Before writing a
nything, ask what the design needs to say, an
d how it can best be said to help the person 
navigate the experience.

Write from the end 
user's side of the screen. Name things by wha
t people control and recognize, never by how 
the system is built. A person manages notific
ations, not webhook config. Describe what som
ething does in plain terms rather than sellin
g it. Being specific is always better than be
ing clever.

Use active voice as default. A c
ontrol should say exactly what happens when i
t's used: "Save changes," not "Submit." An ac
tion keeps the same name through the whole fl
ow, so the button that says "Publish" produce
s a toast that says "Published." The vocabula
ry of an interface is the signposting for som
eone navigating the product. Cohesion and con
sistency are how people learn their way aroun
d.

Treat failure and emptiness as moments fo
r direction, not mood. Explain what went wron
g and how to fix it, in the interface's voice
 rather than a person's. Errors don't apologi
ze, and they are never vague about what happe
ned. An empty screen is an invitation to act.


Keep the register conversational and tuned:
 plain verbs, sentence case, no filler, with 
tone matched to the brand and the audience. L
et each element do exactly one job. A label l
abels, an example demonstrates, and nothing q
uietly does double duty.


