#!/usr/bin/env python3
import subprocess
import sys
import time
import signal
import os

def signal_handler(sig, frame):
    print("\n프로그램을 종료합니다...")
    sys.exit(0)

def main():
    print("F13 복구봇 시작 중...")
    print()
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # new.py 실행
        print("new.py 실행 중...")
        new_process = subprocess.Popen([sys.executable, "new.py"])
        
        # web.py 실행
        print("web.py 실행 중...")
        web_process = subprocess.Popen([sys.executable, "web.py"])
        
        print()
        print("두 스크립트가 모두 실행되었습니다.")
        print("new.py PID:", new_process.pid)
        print("web.py PID:", web_process.pid)
        print("프로세스를 종료하려면 Ctrl+C를 누르세요.")
        
        # 두 프로세스가 종료될 때까지 대기
        new_process.wait()
        web_process.wait()
        
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다...")
        if 'new_process' in locals():
            new_process.terminate()
        if 'web_process' in locals():
            web_process.terminate()
    except Exception as e:
        print(f"오류 발생: {e}")
        if 'new_process' in locals():
            new_process.terminate()
        if 'web_process' in locals():
            web_process.terminate()

if __name__ == "__main__":
    main() 