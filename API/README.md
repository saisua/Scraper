The API folder contains all classes with their necessary pre-call checks and
sanitizing. This introduces performance regression, in exchange of security
and stability in case of accessing this program's features.

If your program depends on the performance of this library, please make use
of the Core/ classes