#!/usr/bin/env bash

N=10
items=./${1}/*
newdir=./black_clothes

i=1
for path in ${items}; do
    files=${path}/original_image/*
    for file in ${files}; do
        if [ $(($RANDOM % 100)) -lt ${N} ]; then
            index=$(printf "%05d" ${i})
            fname=$(basename $file)
            newfname=${fname/[0-9][0-9][0-9][0-9][0-9]/${index}}
            let i++
            mv ${file} $newdir/$newfname
        fi
    done
done

