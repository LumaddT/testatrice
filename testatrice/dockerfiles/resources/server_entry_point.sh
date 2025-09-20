until [ -f /home/servatrice/config/testatrice.ini ]
do
     sleep 0.1;
done

servatrice --config /home/servatrice/config/testatrice.ini;
