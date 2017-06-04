# InspiderNet

This is a tool to analyze networks papers referencing and citing each other. It acts as a web-crawler, extracting information from [inspirehep](http://inspirehep.net/), then uses the [dot language](https://en.wikipedia.org/wiki/DOT_(graph_description_language) to describe the network. The result can then be plotted by [Graphviz Package](http://www.graphviz.org/) and similar programs.

## Screenshots

Plotting a small network of 17 nodes with ```dot```:
![dot](small_dot.png)
Plotting a small network of 17 nodes with ```fdp```:
![fdp](small_fdp.png)


## Features

Right now for each paper, the following items are extracted:

* The inspirehep bibkey (e.g. ```Penati:2009sw```). It should be easy to extend the script to extract other items from the bibtex file which is provided by inspirehep. 
* The inspirehep url of all the papers referenced by the paper under consideration
* The inspirehep url of all the papers which cite the paper under consideration
* The inspirehep url of all the papers which are cocited with the paper under consideration

This info is then used to generate an output in the [dot language](https://en.wikipedia.org/wiki/DOT_(graph_description_language)), describing the connections between (a subset of) the papers considered. This output can then be used by tools like ```dot```, ```fdp```, ```sfdp``` (provided by the [Graphviz Package](http://www.graphviz.org/)) to print the Graph to ```.png```, ```.pdf``` and many more. 

## Limitations/Bugs

* I did not find an API for inspirehep that can offer all of the above pieces of information, so right now the script actually [downloads the html pages and parses them via regular expressions](http://i.imgur.com/gOPS2.png). Very elegant indeed! Any work on this would be very appreciated! 
* This also means that the script is quite slow at the moment, as three pages have to be downloaded (one for the bibtex file, one for the references and one for the citations). The script waits a few seconds after each download as to not strain the inspirehep capacities, so just let in run in the background for a couple of hours and it should be done. 
* The html pages of some papers which are cited by a 1000 others (or reference a similar great number of other papers) will be provided by inspirehep very slowly which can cause the script to skip the download entry (as it believes that the resource can't be reached). This can be somewhat tweaked by setting the ```timeout``` (right now in ```records.py```) to a bigger value.
* Right now all the downloaded information is saved as a python3 [pickle](https://docs.python.org/2/library/pickle.html) of ```Record``` objects. This clearly is the easiest choice, but definitely not the best one for bigger database scales. If anyone wants to implement this more elegantly or provide export possibilities to other database format, this is very welcome.


## Installation

1. Clone this archive VIA, or download it as a ```.zip``` from HERE. It only uses the standard python libraries, so there should be no need install any other packages. 

2. Install graphviz. On most Linux systems this should already be in the repository, so

        sudo apt-get install graphviz

    or similar should do the job.

## Usage

There are usually several steps involved.

1. Run the python script to crawl over an initial set of papers (seeds); let the script extract references and/or citations (as well as the bibkeys). This information will be saved, so that we do not have to redownload it again (unless we want to update).
2. Download the remaining bibkeys (or general bibliographic info) of the referenced/cited papers.  This information will be saved, so that we do not have to redownload it again (unless we want to update).
3. Create the Graph in dot language for (a subset of) the discovered information.
4. Use the ```graphviz``` package to plot a nice graph.

The ```graphviz``` package provides several nice tools that can be used.

* ```dot```: For "Hierarchical" graphcs: ```dot -Tpdf dotfile.dot > dotfile.pdf``` (to generate pdf output) 
* ```fdp```: For "Spring models": ```dfp -Tpdf dotfile.dot > dotfile.pdf``` (to generate pdf output) 
* ```sfdp```: Like ```fdp``` but scales better with bigger networks: ```dfp -Tpdf dotfile.dot > dotfile.pdf``` (to generate pdf output)

## The Dot Output

The output looks something like this:
```
digraph g {
    // Formatting of the whole Graph
	graph [label="inspiderweb 2017-06-03 23:00:18.888432", fontsize=40];
	node[fontsize=20, fontcolor=black, fontname=Arial, shape=box];
	
	// Adding nodes (optional, but we want to have specific labels)
	"344595" [label="Blumlein:1992ej"];
	"1302816" [label="Bevan:2014iga"];
	"278386" [label="Hagiwara:1989gza"];
	"1322383" [label="Aad:2014xea"];
	"1111995" [label="Chatrchyan:2012meb"];
	"153236" [label="Lepage:1980fj"];
	"855936" [label="delAguila:2010mx"];
	"279185" [label="Altarelli:1989ff"];
	
	// Connections
	// Note that we use the id of inspirehep url as id
	
	"278386" -> "153236"; 
	"1428667" -> "424861"; 
	"1428667" -> "344595"; 
	"1428667" -> "26255"; 
	"1302816" -> "677093"; 
	"424861" -> "344595"; 
	"1428667" -> "353517"; 
	"424861" -> "353517"; 
	"1125962" -> "1111995"; 
	"1125962" -> "591241"; 
	"1204603" -> "892770"; 
	"1322383" -> "1125962"; 
}
```
