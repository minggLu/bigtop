num=4

for ((i=1; i<$num; i++)); do
  cat >> nodes.tmp <<EOF
hadoop-$i
EOF
done 






