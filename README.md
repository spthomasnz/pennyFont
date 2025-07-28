Generation of svg outlines of text for signage for Penny's Wedding!
Text to be laser cut.
Using the pokemon font, 

Freetype outline (quadratic beziers) -> Matplotlib Path (conversion from beziers to points) -> Shapely (to buffer the text to be smaller) -> xml (to sort out shapely svg styles) -> svg

Quick & dirty, but did the job. 
