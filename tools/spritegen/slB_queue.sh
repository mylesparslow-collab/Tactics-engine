#!/bin/sh
cd /home/user/tactics-engine/tools/spritegen
while pgrep -f "sheet.py slough_ringwall" >/dev/null; do sleep 5; done
for u in slough_mother_ashgourd slough_teshk slough_eldest_skin slough_skinbanner_elder slough_kesh; do
  python3 sheet.py $u out/slough --tween --style cel --jobs 2 > /tmp/claude-0/-home-user/e6171783-1e19-5fd1-8383-8baebc627213/scratchpad/slB/q_$u.log 2>&1
done
