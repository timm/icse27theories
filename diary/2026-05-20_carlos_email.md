# Email from Carlos — 2026-05-20 (4 days before session)

> From: Carlos P.
> Date: May 20, 2026, 8:31 AM
> To: Tim, Rick

Hi Tim,

Sending your way some useful stuff:

## 1) Datasets

I added 6 datasets (one being Kaiaulu itself) to this Drive:
https://drive.google.com/drive/folders/1CA4eIO6-U4V0SMBQ05VNI-jdnN4ipM02?usp=drive_link

I also did a bit of cleanup for Helix, if you wouldn't mind re-adding
it to Claude.

I found my "hidden stash" of datasets I thought lost in my computer
(lol) from a prior study, so I have a few more to come. These datasets
contain primarily 3 types of data: Source Code, Git Log, and some
form of communication (Mailing List, GitHub, or JIRA).

## 2) Sanity Checks

The nuance in the communication dataset comes into play if you want
to calculate metrics such as bug counts. It would be interesting to
see if Claude states some dataset can be used for more models than
others (should they require bug count) or not. I see this as a sanity
test.

A second sanity test here would happen for models that require both
communication and source code. This would require Claude to use
Kaiaulu's identity match. For JIRA and Mailing Lists this is viable
for the code, but for GitHub it requires an additional data source.
Again, another sanity test.

## 3) Suggestion to Formalize Sanity Checks and making it easier for us

During the call, you asked both I and Rick if what we were seeing
looked familiar. After some thought, I wanted to ask what you think
about this: Could we instruct Claude to, as opposed to write us
several pages of text, provide us with a) R Notebook (.Rmd) + b)
functions in an R file used by the notebook, "consistent to how
Kaiaulu implements functions and analysis in Notebooks"? If Claude
could give us this, then I could simply branch Claude's code in
Kaiaulu and open as a pull request to do code review as I would any
student's code. I imagine this "mode of sanity checking" would also
be useful for the reviewers as supplemental material. This would also
have Claude gives us the flow of functions in Kaiaulu it is using to
compute the models it implemented functions for, and also, in
Notebook format, explains the process along the way.

## 4) URL of Repos to tell Claude to enable more capabilities in Kaiaulu

A few things you may want to "handover" to Claude. It would be
interesting to see if it changes opinion on what models Kaiaulu
support after passing this to it. Kaiaulu is "loosely coupled" to
all of these. It just has functions that asks for the tools path and
system calls them. Provided Claude can setup and run them, I think
it can pull it off letting Kaiaulu use them:

a) Tell it Kaiaulu uses Perceval (https://github.com/chaoss/grimoirelab-perceval)
   as a dependency. Have it call parse_gitlog() or parse_mbox() to see
   if it works. If it can call either functions without ever hearing
   about Perceval, something is off.

b) Likewise, say the same of the Depends tool:
   https://github.com/multilang-depends/depends. parse_dependencies()
   uses this tool through system calls. Another sanity check.

c) For the LOC and etc metrics, you also need this:
   https://github.com/boyter/scc

d) For refactoring detection, give it this:
   https://github.com/tsantalis/RefactoringMiner#running-refactoringminer-from-the-command-line

e) For Gang of Four, give it this jar:
   https://users.encs.concordia.ca/~nikolaos/files/pattern_detection/pattern4.jar

There are more tools but I think this gives good coverage. Note I am
adding GoF back in the mix: It seems Claude does a very good job in
working up the setup to run dependencies. As such, if it can run
Gang of Four on our behalf, then Kaiaulu can also use and do the GoF
detection (the pain in the neck is setup).

## 5) Access to Claude project on VIEW mode?

p.s.: I made a free account and played a bit with Claude. Would it
be possible to share with I and Rick the view mode of the project?
It would be helpful if we could see the interactions to think a bit
offline on the process.
