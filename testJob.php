#!/usr/bin/php
<?php
$payload="";
while($f = fgets(STDIN)) {
    $payload.=$f;
}

print "Got payload: $payload\n";
system("id");
for ($i=1; $i<=10; $i++)
{
    print "Doing stuph $i\n";
    sleep(1);
}
    fwrite(STDERR, "Diz is error\n");
print "Stopping execution with errorcode 123\n";
die(123);
