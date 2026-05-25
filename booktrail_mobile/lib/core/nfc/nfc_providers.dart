import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'nfc_service.dart';

final nfcServiceProvider = Provider<NfcService>((ref) {
  return MethodChannelNfcService();
});
