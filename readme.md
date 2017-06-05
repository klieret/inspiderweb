# InspiderWeb [![Build Status](https://travis-ci.org/klieret/python-colorlog.svg?branch=master)](https://travis-ci.org/klieret/inspiderweb)
[Features](#features) | [Screenshots](#screenshots) | [How does it work?](#how-does-it-work) | [Limitations/Bugs](#limitationsbugs) | [Installation](#installation) | [Usage](#usage) | [Tutorial](#tutorial) | [License](#license)

This is a tool to analyze networks papers referencing and citing each other. It acts as a web-crawler, extracting information from [inspirehep](http://inspirehep.net/), then uses the [dot language](https://en.wikipedia.org/wiki/DOT_(graph_description_language)) to describe the network. The result can then be plotted by the [Graphviz Package](http://www.graphviz.org/) and similar programs.


## Features

* Clickable nodes which open the paper in inspirehep! For this to work, do not use the ```-Tpdf``` option (as it uses cairo which does not support hyperlinks). Instead do ```dot -Tps2 dotfile.dot > tmp.ps && ps2pdf tmp.ps output.pdf```.  
* Sort papers by year!

## Screenshots

A small number of papers which reference each other, sorted by the year the papers were published:
![opening picture](https://github.com/klieret/readme-files/blob/master/inspiderweb/opening.jpg)

A big number of papers which reference each other, sorted by the year the papers were published: [PDF with clickable nodes](https://rawgit.com/klieret/readme-files/master/inspiderweb/clickable_dotfile_huge.pdf).
<!--Small network of some 15 nodes, sorted by year (plotted with ```dot```):-->
<!--![by year](_small_by_year.png)-->
<!--Plotting a small network of 17 nodes with ```dot```:-->
<!--![dot](_small_dot.png)-->
<!--Plotting a small network of 17 nodes with ```fdp```:-->
<!--![fdp](_small_fdp.png)-->


## How does it work?

Right now for each paper, the following items are extracted:

* The inspirehep bibkey (e.g. ```Penati:2009sw```). It should be easy to extend the script to extract other items from the bibtex file which is provided by inspirehep. 
* The inspirehep url of all the papers referenced by the paper under consideration
* The inspirehep url of all the papers which cite the paper under consideration
* The inspirehep url of all the papers which are cocited with the paper under consideration

This info is then used to generate an output in the [dot language](https://en.wikipedia.org/wiki/DOT_(graph_description_language)), describing the connections between (a subset of) the papers considered. This output can then be used by tools like ```dot```, ```fdp```, ```sfdp``` (provided by the [Graphviz Package](http://www.graphviz.org/)) to print the Graph to ```.png```, ```.pdf``` and many more. 

## Limitations/Bugs

* I didn't do too many tests and there's maybe more todo notes in the code than features itself, so don't expect everything to work right away!
* I did not find an API for inspirehep that can offer all of the above pieces of information, so right now the script actually [downloads the html pages and parses them via regular expressions](http://i.imgur.com/gOPS2.png). Very elegant indeed! Any work on this would be very appreciated! 
* This also means that the script is quite slow at the moment, as three pages have to be downloaded (one for the bibtex file, one for the references and one for the citations). The script waits a few seconds after each download as to not strain the inspirehep capacities, so just let in run in the background for a couple of hours and it should be done. 
* The html pages of some papers which are cited by a 1000 others (or reference a similar great number of other papers) will be provided by inspirehep very slowly which can cause the script to skip the download entry (as it believes that the resource can't be reached). This can be somewhat tweaked by setting the ```timeout``` (right now in ```records.py```) to a bigger value.
* Right now all the downloaded information is saved as a python3 [pickle](https://docs.python.org/2/library/pickle.html) of ```Record``` objects. This clearly is the easiest choice, but definitely not the best one for bigger database scales. If anyone wants to implement this more elegantly or provide export possibilities to other database format, this is very welcome.


## Installation

1. Clone this archive via 
        
        git clone https://github.com/klieret/inspiderweb
    
    or download the current version as a ```.zip``` by clicking [here](https://github.com/klieret/inspiderweb/archive/master.zip). 
    I assume you already have ```pythone3``` installed. 
    As for python >= 3.5 it only uses the standard python libraries, for earlier version, you need to install the ```typing``` package, e.g. run
    
        sudo pip3 install typing

2. Install graphviz. On most Linux systems this should already be in the repository, so

        sudo apt-get install graphviz

    or similar should do the job.
    
3. If you need to generate pdfs with clickable hyperlinks, you need the ```ps2pdf``` utility. E.g. run

        sudo apt-get install ps2pdf

## Usage

There are usually several steps involved. See *Tutorial* below for some easy examples.

1. Run the python script to crawl over an initial set of papers (seeds); let the script extract references and/or citations (as well as the bibkeys). This information will be saved, so that we do not have to redownload it again (unless we want to update).
2. Download the remaining bibkeys (or general bibliographic info) of the referenced/cited papers.  This information will be saved, so that we do not have to redownload it again (unless we want to update).
3. Create the Graph in dot language for (a subset of) the discovered information.
4. Use the ```graphviz``` package to plot a nice graph.

The ```graphviz``` package provides several nice tools that can be used.

* ```dot```: For "Hierarchical" graphcs: ```dot -Tpdf dotfile.dot > dotfile.pdf``` (to generate pdf output) 
* ```fdp```: For "Spring models": ```dfp -Tpdf dotfile.dot > dotfile.pdf``` (to generate pdf output) 
* ```sfdp```: Like ```fdp``` but scales better with bigger networks: ```dfp -Tpdf dotfile.dot > dotfile.pdf``` (to generate pdf output)

All command line options are described in the help message: Run ```python3 inspiderweb.py --help``` to get:
```
usage: python3 inspiderweb.py -d DATABASE [DATABASE ...] [-o OUTPUT]
                              [-s SEEDS [SEEDS ...]] [-p]
                              [-u {refs,cites,bib} [{refs,cites,bib} ...]]
                              [-t {refs,cites,bib} [{refs,cites,bib} ...]]
                              [-h] [--rank {year}] [--maxseeds MAXSEEDS]
                              [--forceupdate]

    INSPIDERWEB
 `.,-'\_____/`-.,'     Tool to analyze networks papers referencing and citing each
  /`..'\ _ /`.,'\      other. It acts as a web-crawler, extracting information from
 /  /`.,' `.,'\  \     inspirehep, then uses the dot languageto describe the
/__/__/     \__\__\__  network. The result can then be plotted by the graphviz
\  \  \     /  /  /    Package and similar programs.
 \  \,'`._,'`./  /     More info on the github page
  \,'`./___\,'`./      https://github.com/klieret/inspiderweb
 ,'`-./_____\,-'`.
     /       \

Setup/Configure Options:
  Supply in/output paths...

  -d DATABASE [DATABASE ...], --database DATABASE [DATABASE ...]
                        Pickle database (db) file. Multiple db files are
                        supported. In this case the first one will be used to
                        save the resulting merged db
  -o OUTPUT, --output OUTPUT
                        Output dot file.
  -s SEEDS [SEEDS ...], --seeds SEEDS [SEEDS ...]
                        Input seed file. Multiple seed files are supported.

Action Options:
  What do you want to do?

  -p, --plot            Generate dot output (i.e. plot).
  -u {refs,cites,bib} [{refs,cites,bib} ...], --updateseeds {refs,cites,bib} [{refs,cites,bib} ...]
                        Get specified information for the seeds. Multiple
                        arguments are supported.
  -t {refs,cites,bib} [{refs,cites,bib} ...], --updatedb {refs,cites,bib} [{refs,cites,bib} ...]
                        Get specified information for the records in the
                        database. Multiple arguments are supported.

Misc:
  Misc Options

  -h, --help            Print this help message.
  --rank {year}         Rank by [year]
  --maxseeds MAXSEEDS   Maximum number of seeds (for testing purposes).
  --forceupdate         For all information that we get from the database:
                        Force redownload
```

## Tutorial

In the following I will always give two lines, the second with the shortcut options, the first one with the longer (and easier to understand options). Instead of ```python3 inspiderweb.py```, you can also use ```python3 inspiderweb.py``` linux (after setting the ```x``` privilege). Note that paths that contain spaces must be enclosed in quotation marks.

Displaying the help:

    python3 inspiderweb.py --help
    python3 inspiderweb.py --h
    
Printing statistics about our database (will always be printed if we run the program). It will only be created, so it will look pretty bleak. Of course you can supply your own name for the database, here it's ```test.pickle``` (in the ```db``` folder).

    python3 inspiderweb.py --database db/test.pickle
    python3 inspiderweb.py -d db/test.pickle

Output:

    WARNING: Could not load db from file.
    INFO: ************** DATABASE STATISTICS ***************
    INFO: Current number of records: 0
    INFO: Current number of completed records: 0
    INFO: Current number of records with bibkey: 0
    INFO: **************************************************

Add a few seeds (the ids of inspirehep, i.e. the number ```811388``` from ```http://inspirehep.net/record/811388/```) and download the bibinfo and the references. For this we use the example file in ```seeds/example_small.txt```.

    python3 inspiderweb.py --database db/test.pickle --seeds seeds/example_small.txt --updateseeds bib refs
    python3 inspiderweb.py -d db/test.pickle -s seeds/example_small.txt -u bib refs
   
This can take some time (around 40s, mainly because the script waits quite often to not overload the inspirehep server), while we see output like: 

    INFO: ************** DATABASE STATISTICS ***************
    INFO: Current number of records: 0
    INFO: Current number of completed records: 0
    INFO: Current number of records with bibkey: 0
    INFO: **************************************************
    INFO: Read 11 seeds from file seeds/example_small.txt.
    DEBUG: Successfully saved db to db/test.pickle
    DEBUG: Downloading bibfile of 1125962
    DEBUG: Downloading from http://inspirehep.net/record/1125962/export/hx.
    DEBUG: Download successfull. Sleeping for 3s.
    DEBUG: Bibkey of 1125962 is Chatrchyan:2012gqa
    DEBUG: Downloading references of 1125962
    DEBUG: Downloading from http://inspirehep.net/record/1125962/references.
    DEBUG: Download successfull. Sleeping for 3s.
    DEBUG: 1125962 is citing 44 records
    ...

Afterwards, if we run the statistics again, we could see that we were successfull:

    DEBUG: Successfully loaded db from db/test.pickle
    INFO: ************** DATABASE STATISTICS ***************
    INFO: Current number of records: 10
    INFO: Current number of completed records: 0
    INFO: Current number of records with bibkey: 10
    INFO: **************************************************

Now we are ready to plot the relations between these nodes:

    python3 inspiderweb.py --database db/test.pickle --plot --seeds seeds/example_small.txt --output build/test.dot
    python3 inspiderweb.py -d db/test.pickle -p -s seeds/example_small.txt -o build/test.dot

This will produce the file ```build/test.dot``` (I chose to place all of the output files in the ```build``` repository as to not make the repository dirty):

    digraph g {
        
        // Formatting of the whole Graph
    
        graph [label="inspiderweb 2017-06-04 16:02:09.361469", fontsize=40];
        node[fontsize=20, fontcolor=black, fontname=Arial, style=filled, color=green];	
        
        // Adding nodes (optional, but we want to have specific labels)
        
        "591241" [label="Sullivan:2002jt" URL="http://inspirehep.net/record/591241"];
        "855936" [label="delAguila:2010mx" URL="http://inspirehep.net/record/855936"];
        "1111995" [label="Chatrchyan:2012meb" URL="http://inspirehep.net/record/1111995"];
        "279185" [label="Altarelli:1989ff" URL="http://inspirehep.net/record/279185"];
        "1125962" [label="Chatrchyan:2012gqa" URL="http://inspirehep.net/record/1125962"];
        "892770" [label="Grojean:2011vu" URL="http://inspirehep.net/record/892770"];
        "1322383" [label="Aad:2014xea" URL="http://inspirehep.net/record/1322383"];
        "677093" [label="Schmaltz:2005ky" URL="http://inspirehep.net/record/677093"];
        "1204603" [label="Han:2012vk" URL="http://inspirehep.net/record/1204603"];
        
        // Connections
	
        "1204603" -> "1111995"; 
        "1111995" -> "279185"; 
        "1125962" -> "1111995"; 
        "1125962" -> "591241"; 
        "1322383" -> "591241"; 
        "892770" -> "591241"; 
        "1322383" -> "1125962"; 
        "1125962" -> "677093"; 
        "892770" -> "855936"; 
        "1204603" -> "892770"; 
    }%                               

Note that we could also have done all of the above with just one command:

    python3 inspiderweb.py --database db/test.pickle --plot --seeds seeds/example_small.txt --updateseeds bib refs --output build/test.dot
    python3 inspiderweb.py -d db/test.pickle -p -s seeds/example_small.txt -u bib refs -o build/test.dot

Note that running this should (basically) run straight through, without downloading anything, as all the information was saved in the database: This gives output like

    ...
    DEBUG: Skipping downloading of info.
    DEBUG: Skipping downloading of references.
    DEBUG: Skipping downloading of info.
    DEBUG: Skipping downloading of references.
    DEBUG: Skipping downloading of info.
    DEBUG: Skipping downloading of references.
    DEBUG: Successfully saved db to db/test.pickle
    DEBUG: Skipping downloading of info.
    DEBUG: Skipping downloading of references.
    DEBUG: Skipping downloading of info.
    DEBUG: Skipping downloading of references.
    DEBUG: Skipping downloading of info.
    DEBUG: Skipping downloading of references.
    ...

Now we are ready to use ```dot``` to plot this! The most basic command for ```.pdf``` output is:

    dot -Tpdf build/test.dot > build/test.pdf 

which gives us the following picture: 

![tutorial first picture](https://github.com/klieret/readme-files/blob/master/inspiderweb/tutorial.png)

To get ```.pdf``` output with clickable nodes, we cannot use ```-Tpdf``` however, but instead first have to generate a ```.ps``` which we then convert via the ```ps2pdf``` utility:

    dot -Tps2 build/test.dot > test.ps && ps2pdf build/test.ps build/test.pdf 

To get the graph sorted by years, simply supply the ```--rank year``` option. Doing all of this in one line (connecting different commands with ```&&```):

    python3 inspiderweb.py -d db/test.pickle -p -s seeds/example_small.txt -o build/test.dot && dot -Tps2 build/test.dot > build/test.ps && ps2pdf build/test.ps build/test.pdf 

![tutorial year picture](https://github.com/klieret/readme-files/blob/master/inspiderweb/tutorial_year.png)

## License

MIT license. See file ```license.txt``` enclosed in the repository.
