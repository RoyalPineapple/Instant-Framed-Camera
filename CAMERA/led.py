
#imports
import asyncio
# import RPi.GPIO as GPIO

# def enableLED(v):
#     ledPin = 18
#     GPIO.setmode(GPIO.BCM)
#     GPIO.setwarnings(False)
#     GPIO.setup(ledPin, GPIO.OUT)
#     GPIO.output(ledPin, 1 if v else 0)

class LED:
	stopEvent = asyncio.Event()

	def stop(self):
		self.stopEvent.set()

	def test(self):
		print()

		async def blink(time):
			try:
				on = False
				print("starting blink")
				while True:
					on = not on
					print(f"blink: {on}")
					await asyncio.sleep(time)
			except asyncio.CancelledError:
				print('Blink(): cancel')
				raise
			finally:
				print('ending blink')

		async def wait_for_stop():
			await self.stopEvent.wait()
			print("stopping")

		async def main():
			await asyncio.gather(blink(0.5), wait_for_stop())

		asyncio.run(main())


led = LED()
led.test()
sleep(5)
led.stop()
